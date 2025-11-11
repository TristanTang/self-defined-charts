from flask import Flask, jsonify, request
import pymysql

app = Flask(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'school_database',
    'charset': 'utf8mb4'
}


def get_db_connection():
    try:
        return pymysql.connect(**DB_CONFIG)
    except pymysql.MySQLError as e:
        print(f"Error connecting to MySQL: {e}")
        return None


@app.route('/tables', methods=['GET'])
def get_tables():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"code": -1, "msg": "Failed to connect to database"})
        
        with conn.cursor() as cursor:
            # 获取所有表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()

            result = []
            for table in tables:
                table_name = table[0]
                cursor.execute(
                    f"SELECT TABLE_COMMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA='school_database' AND TABLE_NAME='{table_name}'")
                table_comment = cursor.fetchone()[0] or table_name

                # 获取列信息
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                column_list = []
                for col in columns:
                    cursor.execute(
                        f"SELECT COLUMN_COMMENT FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='school_database' AND TABLE_NAME='{table_name}' AND COLUMN_NAME='{col[0]}'")
                    comment = cursor.fetchone()[0] or col[0]
                    column_list.append({
                        "column_name": col[0],
                        "column_name_cn": comment
                    })

                result.append({
                    "table_name": table_name,
                    "table_name_cn": table_comment,
                    "columns": column_list
                })

            return jsonify({"code": 0, "tables": result})
    except Exception as e:
        return jsonify({"code": -1, "msg": str(e)})
    finally:
        if conn:
            conn.close()


@app.route('/submit_statistics', methods=['POST'])
def submit_statistics():
    try:
        data = request.json
        table_name = data['table_name']
        statistic_column = data['statistic_column_name']
        statistic_function = data['statistic_function']
        group_column = data['group_column_name']

        # 获取数据库连接
        conn = get_db_connection()
        if not conn:
            return jsonify({"code": -1, "msg": "Failed to connect to database"})

        with conn.cursor() as cursor:
            # 动态生成 SQL 查询语句
            sql_step1 = f"""
                SELECT 
                    {statistic_function}({statistic_column}) as stat_value
            """
            if group_column:
                sql_step1 += f"""
                    , {group_column}
                """
            sql_step1 += f"""
                FROM {table_name}
            """
            if group_column:
                sql_step1 += f"""
                GROUP BY {group_column}
            """
            print(f"Step 1 SQL: {sql_step1}")  # 打印第一步SQL以便调试
            cursor.execute(sql_step1)
            step1_result = cursor.fetchall()

            # 如果有分组字段，则基于分组字段查询 student_info 和 class_info 表
            if group_column:
                # 提取分组字段的值
                group_values = [row[1] for row in step1_result]

                # 查询 student_info 表
                if group_column == 'student_id':
                    student_info_sql = f"""
                        SELECT student_id, CONCAT(student_id, '+', student_name) as student_name_cn
                        FROM student_info
                        WHERE student_id IN ({','.join(map(str, group_values))})
                    """
                    print(f"Student Info SQL: {student_info_sql}")  # 打印学生信息SQL以便调试
                    cursor.execute(student_info_sql)
                    student_info_map = {row[0]: row[1] for row in cursor.fetchall()}

                # 查询 class_info 表
                elif group_column == 'class_id':
                    class_info_sql = f"""
                        SELECT class_id, CONCAT(class_id, '+', class_name) as class_name_cn
                        FROM class_info
                        WHERE class_id IN ({','.join(map(str, group_values))})
                    """
                    print(f"Class Info SQL: {class_info_sql}")  # 打印课程信息SQL以便调试
                    cursor.execute(class_info_sql)
                    class_info_map = {row[0]: row[1] for row in cursor.fetchall()}

            # 组装最终结果
            final_result = []
            for row in step1_result:
                stat_value = row[0]
                if group_column:
                    group_value = row[1]
                    if group_column == 'student_id':
                        label = student_info_map.get(group_value, f"未知学号({group_value})")
                    elif group_column == 'class_id':
                        label = class_info_map.get(group_value, f"未知课程号({group_value})")
                else:
                    label = "总统计"
                final_result.append({
                    "label": label,
                    "value": stat_value
                })

            # 返回统一的业务数据格式
            return jsonify({
                "code": 0,
                "data": {
                    "labels": [item["label"] for item in final_result],
                    "values": [item["value"] for item in final_result]
                }
            })

    except Exception as e:
        return jsonify({"code": -1, "msg": str(e)})
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    app.run(debug=True)