
from datetime import datetime

from mongodb_connect import MongoDBConnect


class BorrowManager:
    """借阅流水管理：借阅登记、归还处理、逾期查询"""

    def __init__(self):
        self.client, self.db = MongoDBConnect.getDatabase()
        self.collection = self.db["borrow_logs"]

    def borrow_book(self, reader_card, book_isbn):
        """借阅登记，状态为借出"""
        log = {
            "borrow_date": datetime.now(),
            "reader_card": reader_card,
            "book_isbn": book_isbn,
            "status": "借出"
        }
        result = self.collection.insert_one(log)
        print("insert_one 受影响文档数：", 1 if result.inserted_id else 0)
        print("借阅登记成功，记录 _id：", result.inserted_id)
        return result.inserted_id

    def return_book(self, reader_card, book_isbn):
        """归还处理，把借出状态的记录改为已归还并写入归还时间"""
        result = self.collection.update_many(
            {
                "reader_card": reader_card,
                "book_isbn": book_isbn,
                "status": "借出"
            },
            {
                "$set": {
                    "status": "已归还",
                    "return_date": datetime.now()
                }
            }
        )
        print("update_many 匹配", result.matched_count,
              "条，修改", result.modified_count, "条。")
        return result.modified_count

    def find_all(self, limit=20):
        """查询借阅流水"""
        logs = list(self.collection.find().limit(limit))
        if not logs:
            print("未查询到借阅记录。")
            return logs
        for log in logs:
            print(log.get("reader_card"), "|", log.get("book_isbn"), "|",
                  log.get("status"), "| 借阅时间", log.get("borrow_date"))
        print("共查询到", len(logs), "条记录。")
        return logs

    def find_by_reader(self, reader_card):
        """查询某位读者的全部借阅记录"""
        logs = list(self.collection.find({"reader_card": reader_card}))
        if not logs:
            print("该读者没有借阅记录。")
            return logs
        for log in logs:
            print(log.get("book_isbn"), "|", log.get("status"), "|",
                  log.get("borrow_date"))
        print("共查询到", len(logs), "条记录。")
        return logs

    def find_overdue(self):
        """查询逾期未还记录"""
        logs = list(self.collection.find({"status": "逾期"}))
        if not logs:
            print("当前没有逾期记录。")
            return logs
        for log in logs:
            print(log.get("reader_card"), "|", log.get("book_isbn"), "|",
                  log.get("borrow_date"))
        print("逾期记录共", len(logs), "条。")
        return logs

    def count_by_status(self):
        """按状态统计借阅记录条数"""
        pipeline = [
            {"$group": {"_id": "$status", "数量": {"$sum": 1}}},
            {"$sort": {"数量": -1}}
        ]
        result = list(self.collection.aggregate(pipeline))
        if not result:
            print("借阅流水集合为空。")
            return result
        for item in result:
            print(item["_id"], "：", item["数量"], "条")
        return result

    def close(self):
        self.client.close()
