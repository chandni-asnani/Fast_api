from db.connections import conn


class FetchData:
    
    @staticmethod
    def fetchblacklisteddomains() -> list:
        entity = conn.local.domain.find()
        result = [{"id":str(item["_id"]),"domain":item["domain"]} for item in entity]
        return result