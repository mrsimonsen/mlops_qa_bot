from pipelines.data_ingestion import data_ingestion_pipeline

if __name__ == "__main__":
	print("Executing the data ingestion pipeline...")
	data_ingestion_pipeline()
	print("Pipeline execution has been triggered")