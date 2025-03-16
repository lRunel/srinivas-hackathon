from website import app,db
from flask_login import login_required, current_user
from website.model import User,Skill
from flask import render_template,jsonify,request

@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    user = current_user

    # Fetch up to 3 'learn' skills of the current user
    skills = Skill.query.filter(
        Skill.user_id == user.id, Skill.category == 'learn'
    ).limit(3).all()

    # Find matching users who "know" the skills the current user wants to "learn"
    matching_users = [
        db.session.query(User)
        .join(Skill, User.id == Skill.user_id)
        .filter(Skill.skill_name == skill.skill_name, Skill.category == 'known', User.id != user.id)
        .first()  # Only get one matching user per skill
        for skill in skills
    ]

    # Safe retrieval function to avoid NoneType errors
    def safe_get(lst, index, attr, default=None):
        return getattr(lst[index], attr, default) if len(lst) > index and lst[index] else default

    person1, person2, person3 = (
        safe_get(matching_users, 0, 'name', "No match found"),
        safe_get(matching_users, 1, 'name', "No match found"),
        safe_get(matching_users, 2, 'name', "No match found"),
    )

    user1id, user2id, user3id = (
        safe_get(matching_users, 0, 'id'),
        safe_get(matching_users, 1, 'id'),
        safe_get(matching_users, 2, 'id'),
    )

    return render_template(
        'homepage.html',
        user1id=user1id, user2id=user2id, user3id=user3id,
        person1=person1, person2=person2, person3=person3,
        skill1=skills[0].skill_name if skills else "",
        skill2=skills[1].skill_name if len(skills) > 1 else "",
        skill3=skills[2].skill_name if len(skills) > 2 else ""
    )
@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    skills = Skill.query.filter_by(user_id=user.id).all()

    return render_template('profile.html', user=user, skills=skills)
@app.route('/mskills', methods=['POST'])
@login_required
def skill_management():
    data = request.get_json()
    skills = data.get('skills', [])  # Extract list of skills

    if not skills:
        return jsonify({'error': 'No skills provided'}), 400

      # Debugging log

    # Add each skill to the database
    for skill_data in skills:
        skill_name = skill_data.get('skill')
        category = skill_data.get('category')

        if skill_name and category:
            new_skill = Skill(user_id=current_user.id, skill_name=skill_name, category=category)
            db.session.add(new_skill)

    db.session.commit()  # Commit once after adding all skills

    return jsonify({'message': 'All skills added successfully!'}), 200

@app.route('/mskills', methods=['GET'])
@login_required
def skill_page():
    return render_template('mskills.html')