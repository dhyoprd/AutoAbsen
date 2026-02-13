from src.core.interfaces import IContentGenerator, IAutomationDriver

class ReportService:
    """
    Service Layer: Orchestrates the generation and submission of reports.
    Follows DIP: Depends on abstractions (Interfaces).
    """
    
    def __init__(self, ai_generator: IContentGenerator, driver: IAutomationDriver):
        self.ai = ai_generator
        self.driver = driver

    def process_daily_report(self, context: str, user_activity: str, email: str, password: str) -> bool:
        """
        Full workflow: Generate content -> Submit to portal.
        """
        print("🤖 [1/2] Generating Report Content...")
        try:
            report = self.ai.generate_content(context, user_activity)
            if not report.validate():
                print("❌ Generated report failed validation (too short).")
                return False
            
            print("✅ Report Generated:")
            print(f"   - Activity: {len(report.activity)} chars")
            print(f"   - Learning: {len(report.learning)} chars")
            print(f"   - Obstacles: {len(report.obstacles)} chars")
            
        except Exception as e:
            print(f"❌ AI Generation Error: {e}")
            return False

        print("\n🚀 [2/2] Automating Submission...")
        try:
            success = self.driver.execute_full_flow(email, password, report)
            
            if success:
                print("✅ Report Submitted Successfully!")
            else:
                print("❌ Report Submission Failed.")
            
            return success
            
        except Exception as e:
            print(f"❌ Automation Error: {e}")
            return False
        finally:
            self.driver.close()
