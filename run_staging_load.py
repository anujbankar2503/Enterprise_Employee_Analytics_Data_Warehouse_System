from pathlib import Path

from src.etl.data_synthesizer import DataSynthesizer
from src.etl.staging_loader import StagingLoader

PROJECT_ROOT = Path(__file__).resolve().parent
CSV_PATH = PROJECT_ROOT / "data" / "WA_Fn-UseC_-HR-Employee-Attrition.csv"

def main():
    print("Generating data...")
    synth = DataSynthesizer(CSV_PATH)
    datasets = {
        "stg_hr_employee": synth.scale(100_000),
        "stg_employee_history": synth.generate_history(),
        "stg_project": synth.generate_projects(),
        "stg_assignment": synth.generate_assignments(),
        "stg_review": synth.generate_reviews(),
    }
    loader = StagingLoader()
    loader.truncate_all()
    batch_id = loader.start_batch("IBM_HR_SYNTHETIC")
    total = sum(len(df) for df in datasets.values())
    loaded = 0

    try:
        for table, df in datasets.items():
            n = loader.load_table(table, df, batch_id)
            loaded += n
            print(f"Loaded {n:>8,} rows into {table}")
        loader.finish_batch(batch_id, "SUCCESS", total, loaded)
        print(f"Done. Batch {batch_id}: {loaded:,} rows loaded.")
    except Exception as error:
        loader.finish_batch(batch_id, "FAILED", total, loaded, error=str(error))
        print("Load failed:", error)
        raise
    finally:
        loader.close()


if __name__ == "__main__":
    main()