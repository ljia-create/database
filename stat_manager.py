
from mongodb_connect import MongoDBConnect


class StatManager:
    """统计分析：分类统计、借阅趋势、畅销榜"""

    def __init__(self):
        self.client, self.db = MongoDBConnect.getDatabase()
        self.books = self.db["books"]
        self.borrow_logs = self.db["borrow_logs"]

    def category_stat(self):
        """分类统计：按类别分组，统计库存总量、平均价格、图书数量，按库存总量降序"""
        pipeline = [
            {
                "$group": {
                    "_id": "$category",
                    "库存总量": {"$sum": "$stock"},
                    "平均价格": {"$avg": "$price"},
                    "图书数量": {"$sum": 1}
                }
            },
            {"$sort": {"库存总量": -1}}
        ]
        result = list(self.books.aggregate(pipeline))
        if not result:
            print("图书集合为空，无法统计。")
            return result
        print("类别".ljust(12), "库存总量".ljust(10),
              "平均价格".ljust(10), "图书数量")
        for item in result:
            print(str(item["_id"]).ljust(12),
                  str(item["库存总量"]).ljust(12),
                  str(round(item["平均价格"], 2)).ljust(12),
                  item["图书数量"])
        return result

    def borrow_trend(self):
        """借阅趋势：按年份分组统计借阅量，格式化为"2024年"这样的字符串"""
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y年",
                            "date": "$borrow_date"
                        }
                    },
                    "借阅量": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        result = list(self.borrow_logs.aggregate(pipeline))
        if not result:
            print("借阅流水集合为空，无法统计。")
            return result
        for item in result:
            print(item["_id"], "：", item["借阅量"], "次")
        return result

    def best_sellers(self, limit=5):
        """畅销榜：取借阅次数最多的图书"""
        pipeline = [
            {"$sort": {"borrow_count": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "title": 1,
                    "author": 1,
                    "borrow_count": 1,
                    "rating": 1
                }
            }
        ]
        result = list(self.books.aggregate(pipeline))
        if not result:
            print("图书集合为空，无法统计。")
            return result
        for index, item in enumerate(result, start=1):
            print(index, ".", item.get("title"), "|", item.get("author"),
                  "| 借阅次数", item.get("borrow_count"),
                  "| 评分", item.get("rating"))
        return result

    def merge_category_stat(self):
        """把分类统计结果写入 category_stats 集合"""
        pipeline = [
            {
                "$group": {
                    "_id": "$category",
                    "库存总量": {"$sum": "$stock"},
                    "平均价格": {"$avg": "$price"},
                    "图书数量": {"$sum": 1}
                }
            },
            {
                "$merge": {
                    "into": "category_stats",
                    "whenMatched": "replace",
                    "whenNotMatched": "insert"
                }
            }
        ]
        list(self.books.aggregate(pipeline))
        total = self.db["category_stats"].count_documents({})
        print("统计结果已写入 category_stats 集合，当前共有", total, "条记录。")
        return total

    def close(self):
        self.client.close()
