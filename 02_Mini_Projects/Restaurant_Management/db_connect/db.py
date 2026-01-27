# DB커넥션 객체 생성
import pymysql
def getConnection():
    return pymysql.connect(
        host='34.67.3.16',
        port = 3306,
        user = 'acorn',
        passwd= 'acorn1234',
        use_unicode= True,
        db = 'restaurant',
        charset='utf8',
        autocommit=True
    )
