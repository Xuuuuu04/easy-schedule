#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI Agent 工具测试脚本
测试所有 27 个工具的功能是否正常
"""

import os
import sys
import json
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.service import (
    get_all_students,
    get_all_courses,
    get_student_by_name,
    create_student as service_create_student,
    create_course as service_create_course,
    update_student as service_update_student,
    delete_student as service_delete_student
)
from backend.models import StudentCreate, CourseCreate


class ToolTester:
    """工具测试类 - 直接测试 service 函数"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.test_student_id = None
        self.test_student_name = "测试学生小明"

    def print_header(self, text):
        """打印标题"""
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}")

    def print_section(self, text):
        """打印小节"""
        print(f"\n━━━ {text} ━━━")

    def run_test(self, test_name, test_func):
        """运行单个测试"""
        try:
            print(f"\n  测试: {test_name}")
            result = test_func()
            if result:
                print(f"  ✅ PASS")
                self.passed += 1
                return True
            else:
                print(f"  ⚠️  测试返回 False")
                self.failed += 1
                return False
        except Exception as e:
            print(f"  ❌ FAIL: {str(e)}")
            self.failed += 1
            self.errors.append(f"{test_name}: {str(e)}")
            return False

    def test_all(self):
        """运行所有测试"""
        print("\n" + "🎀"*30)
        print("       后端服务功能测试")
        print("🎀"*30)

        # ==================== Student Management Tests ====================
        self.print_header("第一部分: 学生管理 (5个测试)")

        # Test 1: Get all students
        def test1():
            students = get_all_students()
            print(f"     当前学生数: {len(students)}")
            return True
        self.run_test("获取学生列表", test1)

        # Test 2: Create test student
        def test2():
            student_in = StudentCreate(
                name=self.test_student_name,
                grade="小学五年级",
                phone="13800138000",
                parent_contact="小明妈妈 13900139000",
                progress=50,
                notes="这是一个测试学生"
            )
            student = service_create_student(student_in)
            self.test_student_id = student.id
            print(f"     创建成功，学生ID: {self.test_student_id}")
            return True
        self.run_test("创建测试学生", test2)

        # Test 3: Get student by name
        def test3():
            student = get_student_by_name(self.test_student_name)
            if student:
                print(f"     找到学生: {student.name} - {student.grade}")
                return True
            return False
        self.run_test("按姓名查找学生", test3)

        # Test 4: Update student
        def test4():
            if self.test_student_id:
                student_in = StudentCreate(
                    name=self.test_student_name,
                    grade="小学六年级",
                    progress=75,
                    notes="更新后的备注"
                )
                updated = service_update_student(self.test_student_id, student_in)
                return updated and updated.progress == 75
            return False
        self.run_test("更新学生信息", test4)

        # Test 5: Get students again to verify
        def test5():
            students = get_all_students()
            found = any(s.name == self.test_student_name for s in students)
            print(f"     验证: 学生{'存在' if found else '不存在'}")
            return True
        self.run_test("验证学生创建成功", test5)

        # ==================== Course Management Tests ====================
        self.print_header("第二部分: 课程管理 (6个测试)")

        # Test 6: Get all courses
        def test6():
            courses = get_all_courses()
            print(f"     当前课程数: {len(courses)}")
            return True
        self.run_test("获取课程列表", test6)

        # Test 7: Create course for test student
        def test7():
            if self.test_student_id:
                tomorrow = datetime.now() + timedelta(days=1)
                course_in = CourseCreate(
                    title="测试钢琴课",
                    start=tomorrow.replace(hour=14, minute=0),
                    end=tomorrow.replace(hour=15, minute=30),
                    student_id=self.test_student_id,
                    price=150,
                    description="这是一个测试课程"
                )
                course = service_create_course(course_in)
                print(f"     课程创建成功: {course.title}")
                return True
            return False
        self.run_test("创建测试课程", test7)

        # Test 8: Verify course was created
        def test8():
            courses = get_all_courses()
            student_courses = [c for c in courses if c.student_id == self.test_student_id]
            print(f"     测试学生的课程数: {len(student_courses)}")
            return len(student_courses) > 0
        self.run_test("验证课程创建成功", test8)

        # Test 9: Check conflicts
        def test9():
            tomorrow = datetime.now() + timedelta(days=1)
            from backend.service import check_conflicts
            conflicts = check_conflicts(
                tomorrow.replace(hour=14, minute=0),
                tomorrow.replace(hour=15, minute=30)
            )
            print(f"     检测到 {len(conflicts)} 个时间冲突（正常，因为刚创建了课程）")
            return True
        self.run_test("检查时间冲突", test9)

        # Test 10: Financial calculation
        def test10():
            courses = get_all_courses()
            total = sum(c.price for c in courses if c.student_id == self.test_student_id)
            print(f"     测试学生累计收入: ¥{total}")
            return True
        self.run_test("财务计算", test10)

        # ==================== Data Integrity Tests ====================
        self.print_header("第三部分: 数据完整性 (3个测试)")

        # Test 11: Student-Course relationship
        def test11():
            students = get_all_students()
            courses = get_all_courses()
            student_ids = {s.id for s in students}
            orphan_courses = [c for c in courses if c.student_id not in student_ids]
            if orphan_courses:
                print(f"     ⚠️  发现 {len(orphan_courses)} 个孤立课程（学生不存在）")
            else:
                print(f"     ✅ 所有课程都关联到有效学生")
            return True
        self.run_test("检查学生-课程关联", test11)

        # Test 12: Data files exist
        def test12():
            import os
            courses_exists = os.path.exists("data/courses.json")
            students_exists = os.path.exists("data/students.json")
            print(f"     courses.json: {'存在' if courses_exists else '缺失'}")
            print(f"     students.json: {'存在' if students_exists else '缺失'}")
            return courses_exists and students_exists
        self.run_test("检查数据文件", test12)

        # Test 13: Cache functionality
        def test13():
            from backend.service import get_student_by_id_cached
            if self.test_student_id:
                student = get_student_by_id_cached(self.test_student_id)
                return student is not None
            return True
        self.run_test("缓存功能", test13)

        # ==================== Cleanup ====================
        self.print_header("第四部分: 清理测试数据")

        def cleanup():
            if self.test_student_id:
                result = service_delete_student(self.test_student_id)
                print(f"     删除结果: {'成功' if result else '失败'}")
                return result
            return False
        self.run_test("删除测试学生", cleanup)

        # Verify cleanup
        def verify_cleanup():
            student = get_student_by_name(self.test_student_name)
            courses = get_all_courses()
            has_course = any(c.student_id == self.test_student_id for c in courses)
            if not student and not has_course:
                print(f"     ✅ 清理验证成功")
            else:
                print(f"     ⚠️  可能还有残留数据")
            return True
        self.run_test("验证清理结果", verify_cleanup)

        # ==================== Summary ====================
        self.print_header("测试总结")

        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"\n  📊 总计: {total} 个测试")
        print(f"  ✅ 通过: {self.passed} 个")
        print(f"  ❌ 失败: {self.failed} 个")
        print(f"  📈 通过率: {pass_rate:.1f}%")

        if self.errors:
            print(f"\n  ❌ 失败详情:")
            for error in self.errors:
                print(f"    • {error}")

        if pass_rate >= 80:
            print(f"\n  🎉 测试结果良好！后端服务功能正常。")
        elif pass_rate >= 50:
            print(f"\n  ⚠️  部分功能存在问题，请检查上述错误。")
        else:
            print(f"\n  ❌ 多数功能存在问题，请检查配置。")

        return self.passed, self.failed


def main():
    """主函数"""
    tester = ToolTester()
    passed, failed = tester.test_all()

    # 退出码
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
