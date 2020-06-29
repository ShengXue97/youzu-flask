from app import ma,db

class Question(db.Model):
    __tablename__ = "question"
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.JSON)

class QuestionSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = (
            "id",
            "data",
        )
question_schema = QuestionSchema()
question_schemas =  QuestionSchema(many=True)