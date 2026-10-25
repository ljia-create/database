
from mongodb_connect import MongoDBConnect


class ReaderManager:
    """读者信息管理：信息查询、学院统计、等级分布"""

    def __init__(self):
        self.client, self.db = MongoDBConnect.getDatabase()
        self.collection = self.db["readers"]

    def find_all(self, limit=20):
        """查询全部读者"""
        readers = list(self.collection.find().limit(limit))
        if not readers:
            print("未查询到任何读者。")
            return readers
        for reader in readers:
            print(reader.get("card_no"), "|", reader.get("name"), "|",
                  reader.get("college"), "|", reader.get("level"), "|",
                  reader.get("email"))
        print("共查询到", len(readers), "条记录。")
        return readers

    def find_one(self, card_no):
        """按借阅证号查询读者"""
        reader = self.collection.find_one({"card_no": card_no})
        if reader is None:
            print("未找到借阅证号为", card_no, "的读者。")
        else:
            print(reader)
        return reader

    def count_documents(self, condition=None):
        """统计读者数量"""
        if condition is None:
            condition = {}
        total = self.collection.count_documents(condition)
        print("读者数量：", total)
        return total

    def distinct_colleges(self):
        """获取所有学院名称"""
        colleges = self.collection.distinct("college")
        print("全部学院：", colleges)
        return colleges

    def count_by_college(self):
        """按学院统计读者人数"""
        pipeline = [
            {"$group": {"_id": "$college", "人数": {"$sum": 1}}},
            {"$sort": {"人数": -1}}
        ]
        result = list(self.collection.aggregate(pipeline))
        if not result:
            print("读者集合为空。")
            return result
        for item in result:
            print(item["_id"], "：", item["人数"], "人")
        return result

    def count_by_level(self):
        """按借阅等级统计读者人数"""
        pipeline = [
            {"$group": {"_id": "$level", "人数": {"$sum": 1}}},
            {"$sort": {"人数": -1}}
        ]
        result = list(self.collection.aggregate(pipeline))
        if not result:
            print("读者集合为空。")
            return result
        for item in result:
            print(item["_id"], "：", item["人数"], "人")
        return result

    def close(self):
        self.client.close()
