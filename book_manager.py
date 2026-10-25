
from mongodb_connect import MongoDBConnect


class BookManager:
    """图书信息管理：增删改查、条件检索、评分排行"""

    def __init__(self):
        self.client, self.db = MongoDBConnect.getDatabase()
        self.collection = self.db["books"]

    # ---------- 新增 ----------
    def insert_one(self, book):
        """插入单本图书"""
        result = self.collection.insert_one(book)
        print("insert_one 受影响文档数：", 1 if result.inserted_id else 0)
        print("新增图书 _id：", result.inserted_id)
        return result.inserted_id

    def insert_many(self, books):
        """批量插入图书"""
        result = self.collection.insert_many(books)
        print("insert_many 受影响文档数：", len(result.inserted_ids))
        return result.inserted_ids

    # ---------- 查询 ----------
    def find_all(self, limit=20):
        """查询全部图书"""
        books = list(self.collection.find().limit(limit))
        if not books:
            print("未查询到任何图书。")
            return books
        for book in books:
            print(book)
        print("共查询到", len(books), "条记录。")
        return books

    def find_one(self, isbn):
        """按 ISBN 精确查询单本图书"""
        book = self.collection.find_one({"isbn": isbn})
        if book is None:
            print("未找到 ISBN 为", isbn, "的图书。")
        else:
            print(book)
        return book

    def search(self, category=None, min_price=None, max_price=None,
               min_rating=None, title_keyword=None):
        """多条件组合检索，条件为空则该条件不参与筛选"""
        condition = {}
        if category:
            condition["category"] = category
        if title_keyword:
            condition["title"] = {"$regex": title_keyword}
        if min_price is not None or max_price is not None:
            price = {}
            if min_price is not None:
                price["$gte"] = min_price
            if max_price is not None:
                price["$lte"] = max_price
            condition["price"] = price
        if min_rating is not None:
            condition["rating"] = {"$gte": min_rating}

        books = list(self.collection.find(condition))
        if not books:
            print("没有符合条件的图书，请调整检索条件后重试。")
            return books
        for book in books:
            print(book.get("title"), "|", book.get("category"), "|",
                  book.get("price"), "元 | 评分", book.get("rating"),
                  "| 库存", book.get("stock"))
        print("共查询到", len(books), "条记录。")
        return books

    def top_rating(self, limit=5):
        """按评分降序排行"""
        books = list(self.collection.find().sort("rating", -1).limit(limit))
        if not books:
            print("图书集合为空。")
            return books
        for index, book in enumerate(books, start=1):
            print(index, ".", book.get("title"), "评分", book.get("rating"),
                  "| 借阅次数", book.get("borrow_count"))
        return books

    # ---------- 更新 ----------
    def update_one(self, isbn, update_fields):
        """更新单本图书，update_fields 形如 {"stock": 20}"""
        result = self.collection.update_one(
            {"isbn": isbn},
            {"$set": update_fields}
        )
        print("update_one 匹配", result.matched_count,
              "条，修改", result.modified_count, "条。")
        return result.modified_count

    def increase_stock(self, isbn, amount):
        """调整库存，正数为增加，负数为减少"""
        result = self.collection.update_one(
            {"isbn": isbn},
            {"$inc": {"stock": amount}}
        )
        print("update_one 匹配", result.matched_count,
              "条，修改", result.modified_count, "条。")
        return result.modified_count

    # ---------- 删除 ----------
    def delete_one(self, isbn):
        """按 ISBN 删除单本图书"""
        result = self.collection.delete_one({"isbn": isbn})
        print("delete_one 受影响文档数：", result.deleted_count)
        return result.deleted_count

    def delete_many(self, category):
        """按类别批量删除图书"""
        result = self.collection.delete_many({"category": category})
        print("delete_many 受影响文档数：", result.deleted_count)
        return result.deleted_count

    def close(self):
        self.client.close()
