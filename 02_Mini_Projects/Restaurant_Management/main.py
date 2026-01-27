from flask import Flask, Blueprint, request, render_template, render_template_string, jsonify, session
from flask import redirect, make_response, url_for, flash, get_flashed_messages
import os
import json
import pymysql
import random # 랜덤으로 storecode생성
import string

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import InputRequired, Length
from flask_wtf.csrf import CSRFProtect

from sys_module import menu_search # 메뉴 검색
from werkzeug.security import generate_password_hash, check_password_hash
#비밀번호를 암호화해서 DB에 저장하기 위해 사용

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
CSRFProtect(app) 
app.config['MYSQL_HOST'] = '34.67.3.16' #'localhost' # 클라우드 ip주소로 변경하기 #34.121.238.140 - 쌤ip
app.config['MYSQL_USER'] = "acorn" # DB연결 ID
app.config['MYSQL_PORT'] = 3306 # DB 연결 포트번호
app.config['MYSQL_PASSWORD'] = 'acorn1234' # DB 연결 패스워드
app.config['MYSQL_DB'] = 'restaurant' # 연결할 DB테이블 명

def getConnection():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        port=app.config['MYSQL_PORT'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB'],
        charset='utf8',
        autocommit=True
    ) 

#메인페이지
@app.route("/")
def main():
    if "user" in session: # flask에 session 이 들어 있음.
        storename = menu_search.storeName( user=session["user"] ) # 로그인한 사용자의 가게명 조회
        # 로그인된 사용자
        return render_template("home.html", show_login=False, show_home=True, user=session["user"], storename = storename)  # 로그인 후 들어오는 메인 페이지
    else:
        # 로그인 안 된 사용자
        return render_template("login.html", show_login=True, show_home=False) # 로그인 & 신규 가게 가입 페이지

#로그인 처리
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        userid = request.form["userid"]
        pw = request.form["pw"]

        mysql = getConnection()
        cur = mysql.cursor()
        cur.execute("SELECT * FROM user WHERE userid=%s",(userid,))
        result = cur.fetchone()
        cur.close()
        mysql.close()
        if result and check_password_hash(result[1],pw): #비밀번호 검증
            session["user"]=userid #로그인된 사용자 세션 유지
            return redirect(url_for("main")) # 로그인이 잘 된 경우 main 실행
        else:
            return  render_template_string('''<script>
                           alert("아이디 또는 비밀번호가 올바르지 않습니다.");
                           history.back(); 
                           </script>''') # 알림창만 띄우고 그 전 화면으로 다시 되돌아가기

    return redirect(url_for("main")) #render_template("home.html")

# 로그아웃 처리
@app.route("/logout")
def logout():
    session.pop("user", None) # 로그인정보 삭제
    return redirect(url_for("main"))

# "업체 신규 등록 페이지" 로그인 안 된 사용자에서 업체 신규 등록 버튼을 누른 경우 이동해야할 페이지    
@app.route("/store_insert", methods=['GET','POST']) 
def store_insert():
    return render_template("store_insert.html")

# 로그인 사용자 정보
@app.route("/get_user")
def get_user():
    return jsonify({"user": session.get("user")}) 

# 랜덤 코드 생성
def generate_code():
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    digits = ''.join(random.choices(string.digits, k=3))
    return letters + digits

# "업체 신규 등록 페이지에서 등록 시 수행할 액션
@app.route("/store_insert_action", methods=['POST']) 
def store_insert_action():
    if request.method == "POST":
        storename = request.form["storename"]
        userid = request.form["userid"]
        password = generate_password_hash(request.form["password"])
        storecode = generate_code()
        mysql = getConnection()
        cur = mysql.cursor()
        try:
            data = (userid, password, storecode, 0)
            cur.execute('''insert into store(storecode, storename) values (%s, %s)''', (storecode, storename))
            cur.callproc("user_insert", data)
            mysql.commit()
            result = cur.execute('select @_user_insert_3')
            if result == 1:
                print("등록에 성공하였습니다.")
            elif result == -1:
                print("실패하였습니다.")
            else:
                print("알 수 없는 오류")
        except Exception as e:
            return render_template_string('''
                                <script>
                                   alert("등록에 실패하였습니다.");
                                    history.back();
                                   </script>
                                   ''')
        finally:
            cur.close()
            mysql.close()
    
    return render_template_string('''<script>
                           alert("등록에 성공하였습니다 로그인 후 사용해주세요");
                           window.location.href = "{{ url_for('login') }}";
                           </script>''')


@app.route("/sales_list") # 매출 조회
def sales_list():
    if "user" in session:
        conn = getConnection()
        cur = conn.cursor()
        cur.callproc('sales_ranks')
        storename = menu_search.storeName( user=session["user"] ) # 로그인한 사용자의 가게명 조회
        cur.callproc("menu_select", (storename,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return render_template("sales_list.html", object_list=rows, storename = storename)
    else :
        messages = {
            1: "로그인 해주세요.",
        }
        flash(messages.get(1, "알 수 없는 오류"))
        return  redirect(url_for("main"))  # 로그인 페이지로 이동

@app.route("/sales_insert",methods=["GET", "POST"]) # 매출 등록
def sales_insert():
    storename = menu_search.storeName( user=session["user"] ) # 로그인한 사용자의 가게명 조회
    storeCode = menu_search.storeCode( user=session["user"] ) # 로그인한 사용자의 가게명 코드조회
    if request.method == "GET":
        return render_template("sales_insert.html", storename=storename)
    if request.method == "POST":
        storecode = storeCode 
        menuname = request.form["menuname"]
        price = request.form["price"]
        amount = request.form["amount"]
        conn = getConnection()
        cur = conn.cursor()
        cur.callproc("menu_insert", [menuname, price, amount, storecode, 0])
        cur.execute("SELECT @_menu_insert_4")
        result = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        conn = getConnection()
        cur = conn.cursor()
        cur.callproc('sales_ranks')
        cur.callproc("menu_select", (storename,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        if result == 1:
            return render_template("sales_list.html", object_list=rows, message="등록이 완료되었습니다.")
        else:
            return render_template("sales_list.html", object_list=rows, message="등록 중 오류가 발생했습니다.")

@app.route("/sales_update", methods=["POST"])
def sales_update():
    storename = menu_search.storeName( user=session["user"] ) # 로그인한 사용자의 가게명 조회
    if "amount" not in request.form:  # 수정 페이지 표시
        menuname = request.form["menuname"]
        price = request.form["price"]
        amount = request.form["amount_old"]
        return render_template("sales_update.html",
                               menuname=menuname,
                               price=price,
                               amount=amount)
    menuname = request.form["menuname"]
    new_amount = request.form["amount"]
    conn = getConnection()
    cur = conn.cursor()
    cur.execute("UPDATE menu SET amount=%s, total=price*%s WHERE menuname=%s", (new_amount, new_amount, menuname))
    conn.commit()
    cur.close()
    conn.close()

    conn = getConnection()
    cur = conn.cursor()
    cur.callproc('sales_ranks')
    cur.callproc("menu_select",  (storename,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("sales_list.html", object_list=rows, message="수정이 완료되었습니다.")

@app.route("/sales_delete", methods=["POST"])
def sales_delete():
    storename = menu_search.storeName( user=session["user"] ) # 로그인한 사용자의 가게명 조회
    menuname = request.form["menuname"]
    conn = getConnection()
    cur = conn.cursor()
    cur.callproc("menu_delete", [menuname, 0])
    cur.execute("SELECT @_menu_delete_1")
    conn.commit()
    cur.close()
    conn.close()
    conn = getConnection()
    cur = conn.cursor()
    cur.callproc('sales_ranks')
    cur.callproc("menu_select",(storename,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("sales_list.html", object_list=rows, message="삭제가 완료되었습니다.")

# 히트상품 조회
@app.route("/hitMenu") 
def hitMenu():
    if "user" in session:
        storename = menu_search.storeName( user=session["user"] ) # 로그인한 사용자의 가게명 조회
        topMenuList =menu_search.hitMenu(storename) # 가게명을 넘겨서 top5메뉴 조회
        # JSON 문자열을 파싱
        topMenuList = json.loads(topMenuList)

        return render_template("hit_menu.html", object_list=topMenuList, storename = storename)
    else :
        messages = {
            1: "로그인 해주세요.",
        }
        flash(messages.get(1, "알 수 없는 오류"))
        return  redirect(url_for("main"))  # 로그인 페이지로 이동

    
# 추후에 쓰게 될 수도 있을 것 같아서 만든 메뉴
@app.route("/menu") # 메뉴 관리
def menu():
    return render_template("menu.html")


# 메뉴명 검색
@app.route("/menuSearch", methods=["POST"]) 
def menuSearch():
    result = 0
    if request.method == "POST":
        searchmenu = request.form.get("searchMenu")
        result = menu_search.getSearchMenu(searchmenu, user=session["user"])
    return jsonify(result) # jsong형태로 웹에 데이터 전달
   
# 검색된 메뉴 화면에 표출
@app.route("/viewSearchMenu", methods=["POST"])
def viewSearchMenu():
    if request.method == "POST":
        search_data = request.form.get("searchData") # 서버로 넘겨줄 때 사용한 이름
        # JSON 문자열을 파싱
        parsed_data = json.loads(search_data) #Python의 dict 객체로 변환 // json 형태로 변경하고 싶을 때 dump사용 (json_string = json.dumps(python_object))
        return render_template("view_search_menu.html", data=parsed_data)
    else: # get방식으로 호출 되었을 때 이동할 페이지 --> 연결할 html 생각해보기
        return render_template("view_search_menu.html")

@app.route("/update_store", methods=["POST"])
def update_store():
    storename = menu_search.storeName( user=session["user"] ) # 로그인한 사용자의 가게명 조회
    beforename = storename #request.form["beforename"]
    updatename = request.form["updatename"]
    conn = getConnection()
    cur = conn.cursor()
    cur.callproc("store_update", [beforename, updatename, 0])
    cur.execute("SELECT @_store_update_2")
    result = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    messages = {
        1: "상호명이 성공적으로 수정되었습니다.",
        2: "해당 상호명이 존재하지 않습니다.",
        -1: "오류가 발생했습니다."
    }
    flash(messages.get(result, "알 수 없는 오류"))
    return redirect(url_for("main"))  # render_template("home.html", message=messages.get(result, "알 수 없는 오류"))
    

@app.route("/delete_store", methods=["POST"])
def delete_store():
    storename = menu_search.storeName( user=session["user"] ) # 로그인한 사용자의 가게명 조회
    deletename = storename #request.form["deletename"]
    conn = getConnection()
    cur = conn.cursor()
    cur.callproc("store_delete", [deletename, 0])
    cur.execute("SELECT @_store_delete_1")
    result = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    messages = {
        1: "가게가 성공적으로 삭제되었습니다.",
        2: "삭제할 가게가 존재하지 않습니다.",
        -1: "오류가 발생했습니다."
    }
    flash(messages.get(result, "알 수 없는 오류"))
    return redirect(url_for("logout")) # 로그아웃 시켜서 해당 가게는 다시 가입해야 접속할 수 있도록 함.



# 실행시켜주는 코드
if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True, use_reloader=True)