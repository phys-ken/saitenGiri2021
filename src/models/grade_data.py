"""
採点データに関するデータモデル
"""
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Union


@dataclass
class GradeData:
    """採点データを表すクラス"""
    question_id: str  # 問題ID（例: "Q_0001"）
    student_filename: str  # 学生の解答用紙ファイル名
    score: Optional[Union[int, str]] = None  # 採点結果（整数値またはskip等の文字列）
    
    @property
    def is_graded(self) -> bool:
        """採点済みかどうかを返します"""
        return self.score is not None and self.score != "skip"
    
    @property
    def is_skipped(self) -> bool:
        """スキップされたかどうかを返します"""
        return self.score == "skip"


@dataclass
class GradingSession:
    """採点セッション全体を管理するクラス"""
    grades: Dict[str, Dict[str, GradeData]] = field(default_factory=dict)
    
    def add_grade(self, grade: GradeData) -> None:
        """採点データを追加します"""
        # 問題IDが存在しない場合は初期化
        if grade.question_id not in self.grades:
            self.grades[grade.question_id] = {}
        
        # 問題IDと学生ファイル名のキーでデータを格納
        self.grades[grade.question_id][grade.student_filename] = grade
    
    def get_grade(self, question_id: str, student_filename: str) -> Optional[GradeData]:
        """特定の問題と学生の採点データを取得します"""
        if question_id in self.grades and student_filename in self.grades[question_id]:
            return self.grades[question_id][student_filename]
        return None
    
    def get_student_total_score(self, student_filename: str) -> int:
        """学生の合計点を計算します（未採点項目は除外）"""
        total = 0
        for question_id, grades in self.grades.items():
            if student_filename in grades:
                grade = grades[student_filename]
                if grade.is_graded and isinstance(grade.score, int):
                    total += grade.score
        return total
    
    def get_all_grades_for_student(self, student_filename: str) -> List[GradeData]:
        """学生のすべての採点データを取得します"""
        result = []
        for question_id, grades in self.grades.items():
            if student_filename in grades:
                result.append(grades[student_filename])
        return result
    
    def get_all_grades_for_question(self, question_id: str) -> List[GradeData]:
        """問題のすべての採点データを取得します"""
        if question_id in self.grades:
            return list(self.grades[question_id].values())
        return []
    
    @property
    def student_files(self) -> List[str]:
        """すべての学生ファイル名のリストを返します"""
        student_set = set()
        for question_id, grades in self.grades.items():
            for filename in grades.keys():
                student_set.add(filename)
        return sorted(list(student_set))
    
    @property
    def question_ids(self) -> List[str]:
        """すべての問題IDのリストを返します"""
        return sorted(list(self.grades.keys()))