# Microsoft Qlib Integration

We have successfully integrated the models and feature handlers from [Microsoft/qlib](https://github.com/microsoft/qlib).

## Contents
- `models/`: Contains state-of-the-art deep learning architectures (ALSTM, Transformer, GRU, TabNet) adapted from Qlib.
- `data/`: Contains feature extractors (Alpha158, Alpha360).
- `wrapper.py`: Provides the bridge between Qlib models and the FinPulse AI pipeline.

## Usage
The `pyqlib` package has been added to `requirements.txt`.
You can now substitute the default `XGBoost` pipeline with advanced recurrent models like `ALSTM` or `TransformerModel` by utilizing the `QlibModelTrainer` in `train_xgboost.py`.

*Note: Since Qlib relies on C-extensions, executing these models locally on Windows with AppLocker enabled may be restricted. Run these via GitHub Actions or Docker.*
