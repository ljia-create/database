
from datetime import datetime

from mongodb_connect import MongoDBConnect


class BorrowManager:
    """借阅流水管理：借阅登记、归还处理、逾期查询"""

    def __init__(self):
        self.client, self.db = MongoDBConnect.getDatabase()
        self.collection = self.db["borrow_logs"]

    def borrow_book(self, reader_card, book_isbn):
        """借阅登记。

        先校验图书是否存在且库存大于 0，再用带库存条件的 update_many 原子扣减库存，
        库存扣减成功后才写入借阅流水；若流水写入失败则回滚库存，保证数据一致。
        """
        book = self.db["books"].find_one({"isbn": book_isbn})
        if book is None:
            print("借阅失败：ISBN 为", book_isbn, "的图书不存在。")
            return None
        if int(book.get("stock", 0)) <= 0:
            print("借阅失败：《" + str(book.get("title")) + "》当前库存为 0，无法借阅。")
            return None

        bookResult = self.db["books"].update_many(
            {"isbn": book_isbn, "stock": {"$gt": 0}},
            {"$inc": {"stock": -1, "borrow_count": 1}}
        )
        print("update_many 影响图书：匹配", bookResult.matched_count,
              "条，修改", bookResult.modified_count, "条。")
        if bookResult.modified_count == 0:
            print("借阅失败：库存扣减未生效，请重试。")
            return None

        log = {
            "borrow_date": datetime.now(),
            "reader_card": reader_card,
            "book_isbn": book_isbn,
            "status": "借出"
        }
        try:
            result = self.collection.insert_one(log)
        except Exception as e:
            self.db["books"].update_many(
                {"isbn": book_isbn},
                {"$inc": {"stock": 1, "borrow_count": -1}}
            )
            print("借阅流水写入失败，已回滚库存：", e)
            return None

        print("insert_one 受影响文档数：", 1 if result.inserted_id else 0)
        print("借阅登记成功，记录 _id：", result.inserted_id)
        return result.inserted_id

    def return_book(self, reader_card, book_isbn):
        """归还处理。

        MongoDB 7.0 的时间序列集合不支持直接更新非 metaField 字段
        （borrow_logs 未设置 metaField，任何 update 都会被拒绝），
        因此归还时采用“删除原借出流水 + 写入一条已归还流水”的方式完成状态变更，
        并保留原借阅时间，避免影响按年份的借阅统计。

        为避免同一读者对同一本书存在多条借出记录时被批量删除，
        这里只取其中一条记录，按 _id 精确删除；若新流水写入失败，
        立即把原记录写回，保证历史流水不丢失。
        """
        condition = {
            "reader_card": reader_card,
            "book_isbn": book_isbn,
            "status": "借出"
        }
        record = self.collection.find_one(condition)
        if record is None:
            print("未找到该读者该图书的借出记录，无法归还。")
            return 0

        original = dict(record)
        result = self.collection.delete_one({"_id": record["_id"]})
        print("delete_one 受影响文档数：", result.deleted_count)
        if result.deleted_count == 0:
            print("归还失败：原借出记录删除未生效，请重试。")
            return 0

        newLog = {
            "borrow_date": record.get("borrow_date"),
            "return_date": datetime.now(),
            "reader_card": reader_card,
            "book_isbn": book_isbn,
            "status": "已归还"
        }
        try:
            inserted = self.collection.insert_one(newLog)
        except Exception as e:
            try:
                self.collection.insert_one(original)
                print("归还流水写入失败，已恢复原借出记录：", e)
            except Exception as e2:
                print("归还流水写入失败且原记录恢复失败，请手动核对：", e2)
            return 0

        print("insert_one 受影响文档数：", 1 if inserted.inserted_id else 0)

        bookResult = self.db["books"].update_many(
            {"isbn": book_isbn},
            {"$inc": {"stock": 1}}
        )
        print("update_many 影响图书：匹配", bookResult.matched_count, "条。")
        return result.deleted_count

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
