class Database:
    def __init__(self, db_path):
        self.database = None

    def get_balance_by_phone(self, phone_number: str) -> int or None:
        # self.df = pd.read_excel(database_path)
        # print(self.df.head())
        return 1488 if phone_number != "228" else None
