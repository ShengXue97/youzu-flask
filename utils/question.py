from  models.question import *

def add_questions(questions):
    # here assume the questions format is the list of dict,even only one,still put it in a list.
    for question in questions:            
        q = Question(
            data =question
        )
        db.session.add(q)
    db.session.commit()

def get_questions(filter=None,value=None):
    if filter is None and value is None:
        # no filter or value,pull all the questions
        questions = Question.query.all()
        return [q.data for q in questions]
    elif filter is None or value is None:
        # filter and value should be matched together
        return("wrong enquiry")
    else:
        # for example:filter="Subject",value="Math"
        # if need multiple filter-value pairs,change the filter and value into list or struct them together by dict or.
        questions = Question.query.filter_by(Question.data[filter]==value).all()
        return [q.data for q in questions]
    
