
from mongodb_connect import MongoDBConnect
from book_manager import BookManager
from reader_manager import ReaderManager
from borrow_manager import BorrowManager
from stat_manager import StatManager

MENU = """
========== 图书情报检索与统计平台 ==========
 1. 查看数据库连接状态与集合文档数
 2. 按 ISBN 精确查询图书
 3. 多条件组合检索图书
 4. 图书评分排行榜
 5. 新增图书
 6. 修改图书库存
 7. 删除图书
 8. 查看读者信息
 9. 按学院统计读者人数
10. 按借阅等级统计读者人数
11. 借阅登记
12. 归还处理
13. 查询逾期记录
14. 分类统计（库存总量 / 平均价格 / 图书数量）
15. 借阅趋势统计
16. 畅销榜
17. 分类统计结果落库
 0. 退出
==========================================
"""


def show_status(client, db):
    """打印数据库连接状态与各集合文档总数"""
    client.admin.command("ping")
    print("数据库连接状态：连接成功")
    print("当前数据库：", db.name)
    for name in ["books", "readers", "borrow_logs", "category_stats"]:
        print("集合", name, "文档总数：", db[name].count_documents({}))


def input_int(prompt):
    """读取整数输入，非法输入返回 None"""
    value = input(prompt).strip()
    if value == "":
        return None
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        print("输入格式不正确，请输入数字。")
        return None


def main():
    client = None
    try:
        client, db = MongoDBConnect.getDatabase()
        show_status(client, db)

        book_manager = BookManager()
        reader_manager = ReaderManager()
        borrow_manager = BorrowManager()
        stat_manager = StatManager()

        while True:
            print(MENU)
            choice = input("请选择功能编号：").strip()

            if choice == "1":
                show_status(client, db)

            elif choice == "2":
                isbn = input("请输入 ISBN：").strip()
                book_manager.find_one(isbn)

            elif choice == "3":
                category = input("类别（留空表示不限）：").strip() or None
                min_price = input_int("最低价格（留空表示不限）：")
                max_price = input_int("最高价格（留空表示不限）：")
                min_rating = input_int("最低评分（留空表示不限）：")
                keyword = input("书名关键字（留空表示不限）：").strip() or None
                book_manager.search(category, min_price, max_price,
                                    min_rating, keyword)

            elif choice == "4":
                limit = input_int("显示条数（默认 5）：") or 5
                book_manager.top_rating(int(limit))

            elif choice == "5":
                book = {
                    "isbn": input("请输入 ISBN：").strip(),
                    "title": input("请输入书名：").strip(),
                    "author": input("请输入作者：").strip(),
                    "publisher": input("请输入出版社：").strip(),
                    "category": input("请输入类别：").strip(),
                    "price": input_int("请输入价格：") or 0,
                    "stock": input_int("请输入库存：") or 0,
                    "rating": input_int("请输入评分：") or 0,
                    "borrow_count": 0
                }
                book_manager.insert_one(book)

            elif choice == "6":
                isbn = input("请输入 ISBN：").strip()
                amount = input_int("请输入库存变化量（正数增加，负数减少）：")
                if amount is not None:
                    book_manager.increase_stock(isbn, int(amount))

            elif choice == "7":
                isbn = input("请输入要删除的 ISBN：").strip()
                book_manager.delete_one(isbn)

            elif choice == "8":
                reader_manager.find_all()

            elif choice == "9":
                reader_manager.count_by_college()

            elif choice == "10":
                reader_manager.count_by_level()

            elif choice == "11":
                reader_card = input("请输入借阅证号：").strip()
                book_isbn = input("请输入图书 ISBN：").strip()
                borrow_manager.borrow_book(reader_card, book_isbn)

            elif choice == "12":
                reader_card = input("请输入借阅证号：").strip()
                book_isbn = input("请输入图书 ISBN：").strip()
                borrow_manager.return_book(reader_card, book_isbn)

            elif choice == "13":
                borrow_manager.find_overdue()

            elif choice == "14":
                stat_manager.category_stat()

            elif choice == "15":
                stat_manager.borrow_trend()

            elif choice == "16":
                limit = input_int("显示条数（默认 5）：") or 5
                stat_manager.best_sellers(int(limit))

            elif choice == "17":
                stat_manager.merge_category_stat()

            elif choice == "0":
                print("程序退出，正在关闭数据库连接……")
                break

            else:
                print("无效的功能编号，请重新选择。")

    except Exception as e:
        print("程序运行出现异常：", e)

    finally:
        if client is not None:
            client.close()
            print("数据库连接已关闭。")


if __name__ == "__main__":
    main()
