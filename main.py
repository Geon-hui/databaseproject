from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql

app = Flask(__name__)
app.secret_key = "secret_key"
conn = pymysql.connect(host="localhost", port=3306, user='root', passwd='Kslee8816!', db='db_project', charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)
#mysql 연결, cursorclass를 DictCursor로 설정 -> 딕셔너리 타입으로 SELECT의 결과값들 받아옴
cursor = conn.cursor()
#제어를 위한 커서 가져오기

@app.route('/')
def index():
    global cursor
    sql = "SELECT * FROM board WHERE deleted = %s ORDER BY no DESC"
    userNo = session.get('userNo', 0)
    #board에서 deleted가 ?인 모든 row를 가져오고, no를 기준으로 내림차순으로 정렬한다(최신순)
    cursor.execute(sql, (0,))
    #deleted = %s에서 %s에 0 대입 및 코드 실행
    posts = cursor.fetchall()
    #결과값 받아오기
    return render_template('index.html', posts=posts, logined=userNo!=0)
    #렌더링


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        sql = "SELECT EXISTS(SELECT 1 FROM users WHERE email = %s) as result"
        #email이 ?인 유저가 존재하면 result=1, 아니면 result=0을 리턴
        cursor.execute(sql, (email,))
        result = cursor.fetchone()['result']
        if result: #result=1일 경우 = 이미 유저가 존재할 경우
            flash('이미 사용 중인 이메일입니다.')
            return redirect(url_for('signup'))


        sql  = "INSERT INTO users (user_name, email, hashed_pw) VALUES (%s, %s, %s)"
        #user 추가 코드
        cursor.execute(sql, (username, email, password))
        #%s에 각 값들 대입(튜플 이용)하여 실행
        conn.commit()
        #db commit하여 실제 db에 반영
        flash('회원가입이 완료되었습니다.')
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        sql = "SELECT * FROM users WHERE email = %s"
        cursor.execute(sql, (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['hashed_pw'], password):
            session['user_id'] = user['user_no']
            session['username'] = user['user_name']
            session['userNo'] = user['user_no']
            flash('로그인 성공!')
            return redirect(url_for('index'))
        flash('이메일 또는 비밀번호가 잘못되었습니다.')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('로그아웃되었습니다.')
    return redirect(url_for('index'))


@app.route('/post/<int:post_id>')
def post(post_id):
    sql = "SELECT * FROM board where no = %s"
    cursor.execute(sql, (post_id,))
    post = cursor.fetchone()
    sql = "SELECT user_name FROM users WHERE user_no = %s"
    cursor.execute(sql, (post['writer'],))
    writer = cursor.fetchone()['user_name']
    if not post: #게시글이 없을 경우
        flash("존재하지 않는 게시글입니다.")
        redirect(url_for('index'))
        #에러 메세지와 함께 index로 돌아감
    return render_template('post.html', post=post, writer=writer)


@app.route('/post/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        book = request.form['book']
        writer = session.get('userNo', 0)

        sql = "INSERT INTO board (writer, title, content, book) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (writer, title, content, book))
        conn.commit()
        flash('게시글이 등록되었습니다.')
        return redirect(url_for('index'))
    sql = "SELECT * from books"
    cursor.execute(sql)
    books=cursor.fetchall()
    return render_template('write.html', post={"title": "", "content": ""}, newpost=True, books=books)


@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    sql = "SELECT * FROM board where no = %s"
    cursor.execute(sql, (post_id,))
    post = cursor.fetchone()
    if not post:
        flash("존재하지 않는 게시글입니다.")
        redirect(url_for('index'))
    userNo = session['userNo']
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        if post['writer']!=userNo:
            flash("수정 권한이 없습니다.")
            redirect(url_for('index'))
        sql = "UPDATE board SET title = %s, content = %s WHERE no = %s"
        cursor.execute(sql, (title, content, post_id))
        conn.commit()
        post['title'] = title
        post['content'] = content
        flash('게시글이 수정되었습니다.')
        return redirect(url_for('post', post_id=post_id))
    return render_template('write.html', post=post, newpost=False)

@app.route('/addBook', methods=['GET', 'POST'])
def new_book():
    if request.method == 'POST':
        booktitle = request.form['title']
        author = request.form['author']
        pubyear = request.form['pubyear']
        sql = "INSERT INTO book (title, author, pubyear) VLAUES (%s, %s, %s)"
        cursor.execute(sql, (booktitle, author, pubyear))
        conn.commit()
        flash("도서 등록이 완료되었습니다")
        redirect(url_for('index'))
    return render_template('newbook.html')


@app.route('/post/<int:post_id>/delete')
def delete_post(post_id):
    sql = "SELECT * FROM board where no = %s"
    cursor.execute(sql, (post_id,))
    userNo = session['userNo']
    post = cursor.fetchone()
    if not post:
        flash("존재하지 않는 게시글입니다.")
        redirect(url_for('index'))
    if post['writer'] != userNo:
        flash("수정 권한이 없습니다.")
        redirect(url_for('index'))
    sql = "UPDATE board SET deleted = %s WHERE no = %s"
    cursor.execute(sql, (1, post_id))
    conn.commit()
    flash('게시글이 삭제되었습니다.')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)