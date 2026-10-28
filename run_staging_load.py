from src.etl.data_synthesizer import DataSynthesizer
from src.etl.staging_loader import StagingLoader

CSV_PATH = "data/WA_Fn-UseC_-HR-Employee-Attrition.csv"

print("Generating data...")
synth = DataSynthesizer(CSV_PATH)
employees = synth.scale(100_000)
history = synth.generate_history()
projects = synth.generate_projects()
assignments = synth.generate_assignments()
reviews = synth.generate_reviews()

datasets = {
    "stg_hr_employee": employees,
    "stg_employee_history": history,
    "stg_project": projects,
    "stg_assignment": assignments,
    "stg_review": reviews,
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
except Exception as e:
    loader.finish_batch(batch_id, "FAILED", total, loaded, error=str(e))
    print("Load failed:", e)
    raise
finally:
    loader.close()