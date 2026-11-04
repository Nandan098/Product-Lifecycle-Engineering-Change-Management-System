from core.seed import seed_demo_data
from core.config import project_path
from services.analytics_service import export_powerbi_csv

if __name__ == "__main__":
    seed_demo_data()
    files = export_powerbi_csv(project_path("exports"))
    print("Exported:")
    for file in files:
        print(f"- {file}")
