"""Definicion de las redes (CNN propia y transferencia con MobileNetV3-small congelada + cabeza lineal) y su entrenamiento en CPU.
Cada red recibe uint8 NHWC (0-255) y devuelve LOGITS; `con_softmax` anade el softmax para exportar probabilidades.
El preprocesado (a float, reescalado en el grafo, normalizacion) va DENTRO del modelo: la API solo entrega pixeles."""
import copy
import os
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from comun import TRABAJO, SEMILLA

os.environ.setdefault('TORCH_HOME', str(TRABAJO / 'torch_home'))   # pesos de MobileNet en _trabajo, no en el perfil del usuario
IMN_MEDIA, IMN_STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)


class Prep(nn.Module):
    def __init__(self, lado, media, std):
        super().__init__()
        self.lado = lado
        self.register_buffer('m', torch.tensor(media).view(1, 3, 1, 1))
        self.register_buffer('s', torch.tensor(std).view(1, 3, 1, 1))

    def forward(self, x):                      # x: uint8 N,H,W,3
        x = x.permute(0, 3, 1, 2).float() / 255.0
        if x.shape[-1] != self.lado:
            x = F.interpolate(x, size=(self.lado, self.lado), mode='bilinear', align_corners=False)
        return (x - self.m) / self.s


def bloque(i, o):
    return [nn.Conv2d(i, o, 3, padding=1, bias=False), nn.BatchNorm2d(o), nn.ReLU(inplace=True)]


class CNNPropia(nn.Module):
    """Cuatro bloques convolucionales, promedio global y capa lineal. lado=32 -> 3 reducciones; lado=64 -> 4."""

    def __init__(self, lado):
        super().__init__()
        self.prep = Prep(lado, (0.5,) * 3, (0.5,) * 3)
        capas = bloque(3, 32) + bloque(32, 32) + [nn.MaxPool2d(2)] + bloque(32, 64) + bloque(64, 64) + [nn.MaxPool2d(2)] + bloque(64, 128)
        if lado >= 64:
            capas += [nn.MaxPool2d(2)] + bloque(128, 128)
        capas += [nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Dropout(0.3), nn.Linear(128 if lado < 64 else 128, 2)]
        self.cuerpo = nn.Sequential(*capas)

    def forward(self, x):
        return self.cuerpo(self.prep(x))


class Transferencia(nn.Module):
    def __init__(self, lado, rasgos, cabeza):
        super().__init__()
        self.prep = Prep(lado, IMN_MEDIA, IMN_STD)
        self.rasgos, self.cabeza = rasgos, cabeza

    def forward(self, x):
        return self.cabeza(torch.flatten(self.rasgos(self.prep(x)), 1))


class ConSoftmax(nn.Module):
    def __init__(self, red):
        super().__init__()
        self.red = red

    def forward(self, x):
        return torch.softmax(self.red(x), dim=1)


def mobilenet_rasgos():
    from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights
    m = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.IMAGENET1K_V1).eval()
    return nn.Sequential(m.features, m.avgpool)       # 576 rasgos


def proba(red, x, lote=256):
    red.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(x), lote):
            out.append(torch.softmax(red(torch.from_numpy(x[i:i + lote])), 1).numpy())
    return np.concatenate(out)


def entrenar_cnn(lado, x_tr, y_tr, x_va, y_va, epocas, log):
    torch.manual_seed(SEMILLA)
    red = CNNPropia(lado)
    n_par = sum(p.numel() for p in red.parameters())
    # reescalado una sola vez (misma operacion que en el grafo) para no repetirlo por epoca
    with torch.no_grad():
        xt = torch.cat([red.prep(torch.from_numpy(x_tr[i:i + 512])) for i in range(0, len(x_tr), 512)])
    yt = torch.from_numpy(y_tr)
    opt = torch.optim.AdamW(red.parameters(), lr=3e-3, weight_decay=1e-3)
    lote = 128
    pasos = epocas * ((len(xt) + lote - 1) // lote)
    sch = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=3e-3, total_steps=pasos)
    mejor, mejor_est, curva = -1, None, []
    g = torch.Generator().manual_seed(SEMILLA)
    t0 = time.perf_counter()
    for ep in range(epocas):
        red.train()
        perm = torch.randperm(len(xt), generator=g)
        for i in range(0, len(xt), lote):
            b = perm[i:i + lote]
            xb, yb = xt[b], yt[b]
            volteo = torch.rand(len(b), generator=g) < 0.5
            xb = torch.where(volteo.view(-1, 1, 1, 1), xb.flip(3), xb)
            dx, dy = [int(v) for v in torch.randint(-3, 4, (2,), generator=g)]
            xb = torch.roll(xb, shifts=(dy, dx), dims=(2, 3))
            opt.zero_grad()
            F.cross_entropy(red.cuerpo(xb), yb).backward()
            opt.step(); sch.step()
        red.eval()
        with torch.no_grad():
            pv = proba(red, x_va).argmax(1)
        acc = float((pv == y_va).mean())
        curva.append(round(acc, 4))
        log(f'    epoca {ep + 1:2d}/{epocas}  val={acc:.4f}  t={time.perf_counter() - t0:.0f}s')
        if acc > mejor:
            mejor, mejor_est = acc, copy.deepcopy(red.state_dict())
    seg = time.perf_counter() - t0
    red.load_state_dict(mejor_est)
    return red, {'parametros': n_par, 'epocas': epocas, 'segundos_entrenamiento': round(seg, 1), 'val_por_epoca': curva,
                 'mejor_val': round(mejor, 4)}


def rasgos_de(red_rasgos, lado, x, lote=128):
    prep = Prep(lado, IMN_MEDIA, IMN_STD).eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(x), lote):
            out.append(torch.flatten(red_rasgos(prep(torch.from_numpy(x[i:i + lote]))), 1).numpy())
    return np.concatenate(out)


def entrenar_transferencia(lado, x_tr, y_tr, x_va, y_va, log):
    from sklearn.linear_model import LogisticRegression
    rr = mobilenet_rasgos()
    t0 = time.perf_counter()
    f_tr, f_va = rasgos_de(rr, lado, x_tr), rasgos_de(rr, lado, x_va)
    t_rasgos = time.perf_counter() - t0
    t1 = time.perf_counter()
    mejor, mejor_c, mejor_m = -1, None, None
    for c in (0.01, 0.1, 1.0, 10.0):
        m = LogisticRegression(C=c, max_iter=3000).fit(f_tr, y_tr)
        acc = float((m.predict(f_va) == y_va).mean())
        log(f'    C={c:<5} val={acc:.4f}')
        if acc > mejor:
            mejor, mejor_c, mejor_m = acc, c, m
    t_cabeza = time.perf_counter() - t1
    cabeza = nn.Linear(576, 2)
    w, b = mejor_m.coef_[0], mejor_m.intercept_[0]       # regresion binaria -> dos logits equivalentes (-z/2, +z/2)
    with torch.no_grad():
        cabeza.weight.copy_(torch.tensor(np.stack([-w / 2, w / 2]), dtype=torch.float32))
        cabeza.bias.copy_(torch.tensor([-b / 2, b / 2], dtype=torch.float32))
    red = Transferencia(lado, rr, cabeza).eval()
    return red, {'segundos_rasgos_train_val': round(t_rasgos, 1), 'segundos_ajuste_cabeza': round(t_cabeza, 1),
                 'segundos_entrenamiento': round(t_rasgos + t_cabeza, 1), 'C': mejor_c, 'mejor_val': round(mejor, 4),
                 'parametros_totales': sum(p.numel() for p in red.parameters()), 'lado_entrada_red': lado}


def tiempo_inferencia_torch(red, x1, n=200):
    red.eval()
    xt = torch.from_numpy(x1[:1])
    with torch.no_grad():
        for _ in range(20):
            red(xt)
        t = []
        for _ in range(n):
            a = time.perf_counter(); red(xt); t.append(time.perf_counter() - a)
    t = np.array(t) * 1000
    return {'mediana_ms': round(float(np.median(t)), 2), 'p95_ms': round(float(np.percentile(t, 95)), 2)}
