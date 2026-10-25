
from pymongo import MongoClient


class MongoDBConnect:
    # 虚拟机MongoDB连接地址
    host = "192.168.121.134"
    port = 27016

    # 启用访问控制后必须使用带认证的账号连接
    # libWriter 拥有 readWrite 与 dbAdmin 角色，可读写 library 库
    username = "libWriter"
    password = "Writer123"
    authSource = "library"

    # 业务数据库
    dbName = "library"

    # 统一在模块内拼装连接串，供所有程序文件调用
    default_uri = (
        "mongodb://{0}:{1}@{2}:{3}/?authSource={4}&directConnection=true"
    ).format(username, password, host, port, authSource)

    @staticmethod
    def getConnect(uri=default_uri):
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            directConnection=True
        )
        return client

    @staticmethod
    def getDatabase(uri=default_uri, dbName=dbName):
        client = MongoDBConnect.getConnect(uri)
        return client, client[dbName]


if __name__ == "__main__":
    client = None

    try:
        client = MongoDBConnect.getConnect()

        # 检查数据库连接
        client.admin.command("ping")
        print("MongoDB连接成功！")

        # 查看数据库列表
        databaseNames = client.list_database_names()
        print("当前数据库列表：")

        for name in databaseNames:
            print(name)

        # 查看业务库中的集合
        db = client[MongoDBConnect.dbName]
        print("library 库中的集合：")
        for name in db.list_collection_names():
            print(" -", name)

    except Exception as e:
        print("MongoDB连接失败：", e)

    finally:
        if client is not None:
            client.close()
            print("数据库连接已关闭。")
