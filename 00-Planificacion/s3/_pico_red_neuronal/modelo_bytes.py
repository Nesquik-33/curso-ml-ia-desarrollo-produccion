"""Modelo pyfunc que recibe BYTES de imagen (JPEG/PNG...), los prepara con el mismo preprocesado del entrenamiento y llama a ONNX Runtime.
Se registra con `mlflow.pyfunc.log_model` (modelo desde codigo). Entrada: columna binaria `imagen`. Salida: probabilidades (n, 2) [gato, perro]."""
import io
import json

import mlflow
import numpy as np
from mlflow.pyfunc import PythonModel


class ModeloImagen(PythonModel):
    def load_context(self, context):
        import onnxruntime as ort
        o = ort.SessionOptions()
        o.intra_op_num_threads = 2
        self.sesion = ort.InferenceSession(context.artifacts['onnx'], o, providers=['CPUExecutionProvider'])
        self.nombre = self.sesion.get_inputs()[0].name
        self.lado = int(self.sesion.get_inputs()[0].shape[1])

    def predict(self, context, model_input, params=None):
        from PIL import Image
        from comun import preparar_imagen
        col = model_input['imagen'] if hasattr(model_input, 'columns') else model_input
        lote = np.stack([preparar_imagen(Image.open(io.BytesIO(b)), self.lado) for b in col])
        return self.sesion.run(None, {self.nombre: lote})[0]


mlflow.models.set_model(ModeloImagen())
