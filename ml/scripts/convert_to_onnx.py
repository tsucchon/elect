"""
LightGBMモデルをONNX形式に変換するスクリプト

Vercel Serverless Functions対応のため、libgomp依存のない
onnxruntimeで実行できる形式に変換します。
"""

import joblib
from pathlib import Path
import numpy as np

# ONNX変換用ライブラリ
try:
    from skl2onnx import to_onnx
    from skl2onnx.common.data_types import FloatTensorType
    import onnxmltools
    from onnxmltools.convert import convert_lightgbm
except ImportError as e:
    print("必要なライブラリをインストールしてください:")
    print("pip install onnxmltools skl2onnx")
    print(f"Error: {e}")
    exit(1)


def convert_model_to_onnx(model_path: Path, output_path: Path, feature_count: int):
    """
    LightGBMモデルをONNX形式に変換

    Args:
        model_path: 元のpklファイルのパス
        output_path: 出力するonnxファイルのパス
        feature_count: 特徴量の数
    """
    print(f"Loading model from {model_path}...")
    model_data = joblib.load(model_path)

    lgb_model = model_data['model']
    feature_cols = model_data['feature_cols']
    metrics = model_data['metrics']

    print(f"Model loaded. Features: {len(feature_cols)}, MAPE: {metrics['mape']:.2f}%")

    # ONNX形式に変換
    print("Converting to ONNX format...")

    # 初期タイプを定義（float32の入力テンソル）
    initial_type = [('float_input', FloatTensorType([None, len(feature_cols)]))]

    # LightGBMモデルをONNXに変換
    onnx_model = convert_lightgbm(
        lgb_model,
        initial_types=initial_type,
        target_opset=12
    )

    # ONNXモデルを保存
    print(f"Saving ONNX model to {output_path}...")
    with open(output_path, "wb") as f:
        f.write(onnx_model.SerializeToString())

    # メタデータも保存（特徴量名とメトリクス）
    metadata = {
        'feature_cols': feature_cols,
        'metrics': metrics
    }
    metadata_path = output_path.with_suffix('.metadata.pkl')
    joblib.dump(metadata, metadata_path)

    print(f"✓ ONNX model saved: {output_path}")
    print(f"✓ Metadata saved: {metadata_path}")


def main():
    """メイン処理"""
    # モデルディレクトリ
    model_dir = Path(__file__).parent.parent / "models"

    # 発電量予測モデルを変換
    gen_model_path = model_dir / "generation_tokyo.pkl"
    if gen_model_path.exists():
        print("\n=== Converting Generation Model ===")
        convert_model_to_onnx(
            gen_model_path,
            model_dir / "generation_tokyo.onnx",
            feature_count=20  # 特徴量数
        )
    else:
        print(f"Generation model not found: {gen_model_path}")

    # 価格予測モデルを変換
    price_model_path = model_dir / "price_tokyo.pkl"
    if price_model_path.exists():
        print("\n=== Converting Price Model ===")
        convert_model_to_onnx(
            price_model_path,
            model_dir / "price_tokyo.onnx",
            feature_count=20  # 特徴量数
        )
    else:
        print(f"Price model not found: {price_model_path}")

    print("\n✓ Conversion completed!")
    print("\nNext steps:")
    print("1. Update requirements.txt to include onnxruntime")
    print("2. Update model_loader.py to load ONNX models")
    print("3. Update predictor.py to use ONNX runtime for inference")


if __name__ == "__main__":
    main()
