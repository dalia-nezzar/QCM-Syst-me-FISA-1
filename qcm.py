import streamlit as st
import json
import random
from difflib import SequenceMatcher

st.set_page_config(page_title="QCM - Système", layout="centered")

def calculate_similarity(user_answer, correct_answer):
    """Calcule le pourcentage de similarité entre deux réponses"""
    user_words = set(user_answer.lower().strip().split())
    correct_words = set(correct_answer.lower().strip().split())
    
    if len(correct_words) == 0:
        return 1.0 if len(user_words) == 0 else 0.0
    
    intersection = len(user_words & correct_words)
    similarity = intersection / len(correct_words)
    
    return similarity

def is_answer_correct(q, user_answer):
    """Retourne True si la réponse de l'utilisateur est correcte"""
    if q["type"] == "free_answer":
        user_answers_normalized = [ans.lower().strip() for ans in user_answer if ans.strip()]
        correct_normalized = [c.lower().strip() for c in q["correct"]]

        if len(user_answers_normalized) == 0:
            return False

        if q.get("number_of_answers", 1) > 1:
            combined_answer = " ".join(user_answers_normalized)
            return any(
                combined_answer == correct or calculate_similarity(combined_answer, correct) >= 0.8
                for correct in correct_normalized
            )

        return any(
            ans == correct or calculate_similarity(ans, correct) >= 0.8
            for ans in user_answers_normalized
            for correct in correct_normalized
        )
    else:
        return set(user_answer) == set(q["correct"])

st.title("Questionnaire à choix multiples")

# Initialiser l'état de session
if "current_question" not in st.session_state:
    st.session_state.current_question = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "show_result" not in st.session_state:
    st.session_state.show_result = False
if "started" not in st.session_state:
    st.session_state.started = False
if "num_questions_selected" not in st.session_state:
    st.session_state.num_questions_selected = None
if "question_file" not in st.session_state:
    st.session_state.question_file = "questions.json"
if "shuffled_options" not in st.session_state:  
    st.session_state.shuffled_options = {}

parts = {
    "Chapitre 1 - Rappel sur les systèmes d'exploitation": "rappel-os.json",
    "Chapitre 2 - Le métier d'administrateur système": "metier-admin.json",
    "Chapitre 3 - DHCP et DNS": "dhcp-dns.json",
    "Chapitre 4 - LDAP": "ldap.json",
    "Chapitre 5 - Active Directory": "active-directory.json",
    "Chapitre 6 - NFS - Samba": "nfs-samba.json",
    "Chapitre 7 - FTP": "ftp.json",
    "Chapitre 8 - SSH": "ssh.json",
}

if not st.session_state.started:
    st.write("")
    st.write("")
    st.info("👋 Bienvenue dans ce QCM d'entraînement !")
    st.write("Choisissez la partie à utiliser puis le nombre de questions :")

    selected_part_label = st.selectbox(
        "Choix de la partie:",
        options=list(parts.keys()),
        index=0,
        label_visibility="collapsed"
    )
    selected_file = parts[selected_part_label]

    with open(selected_file, "r", encoding="utf-8") as f:
        part_questions = json.load(f)

    num_questions = st.selectbox(
        "Sélectionnez le nombre de questions:",
        options=list(range(1, len(part_questions) + 1)),
        index=len(part_questions) - 1,
        label_visibility="collapsed"
    )

    st.write("")
    if st.button("🚀 Commencer", use_container_width=True):
        st.session_state.started = True
        st.session_state.num_questions_selected = num_questions
        st.session_state.question_file = selected_file
        st.session_state.question_order = list(range(len(part_questions)))
        random.shuffle(st.session_state.question_order)
        st.session_state.question_order = st.session_state.question_order[:num_questions]
        
        st.session_state.shuffled_options = {}
        for q in part_questions:
            if q["type"] == "multiple_choice":
                shuffled = q["options"].copy()
                random.shuffle(shuffled)
                st.session_state.shuffled_options[q["id"]] = shuffled
        
        st.rerun()
else:
    with open(st.session_state.question_file, "r", encoding="utf-8") as f:
        all_questions = json.load(f)

    current_question_idx = st.session_state.question_order[st.session_state.current_question]
    current_q = all_questions[current_question_idx]

if st.session_state.started and not st.session_state.submitted:
    st.subheader(f"Question {st.session_state.current_question + 1}/{len(st.session_state.question_order)}")
    st.write(current_q["question"])
    
    if current_q["type"] == "multiple_choice":
        options_to_display = st.session_state.shuffled_options.get(current_q["id"], current_q["options"])
        
        if len(current_q["correct"]) > 1:
            st.write("*Plusieurs réponses possibles*")
            selected_answers = []
            for option in options_to_display:
                if st.checkbox(option, key=f"question_{current_q['id']}_{option}"):
                    selected_answers.append(option)
            st.session_state.answers[current_q["id"]] = selected_answers
        else:
            selected_answer = st.radio(
                "Choisir une réponse:",
                options_to_display,
                key=f"question_{current_q['id']}"
            )
            st.session_state.answers[current_q["id"]] = [selected_answer]
    
    elif current_q["type"] == "free_answer":
        num_answers = current_q.get("number_of_answers", 1)
        
        if num_answers > 1:
            st.write(f"*Fournissez {num_answers} réponses*")
        
        answers_list = []
        for i in range(num_answers):
            answer = st.text_input(
                f"Réponse {i + 1}:" if num_answers > 1 else "Votre réponse:",
                key=f"question_{current_q['id']}_answer_{i}"
            )
            answers_list.append(answer)
        
        st.session_state.answers[current_q["id"]] = answers_list
    
    if st.button("✅ Valider cette question"):
        st.session_state.show_result = True
        st.rerun()

if st.session_state.show_result and not st.session_state.submitted:
    st.divider()
    st.subheader("Résultat")
    
    user_answer = st.session_state.answers.get(current_q["id"], [])
    is_correct = is_answer_correct(current_q, user_answer)
    
    st.write(f"**Votre réponse:** {', '.join(user_answer) if user_answer else 'Non répondu'}")
    st.write(f"**Bonne(s) réponse(s):** {', '.join(current_q['correct'])}")
    
    if is_correct:
        st.success("✅ Correct !")
    else:
        st.error("❌ Incorrect !")
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.current_question > 0:
            if st.button("⬅️ Précédent"):
                st.session_state.current_question -= 1
                st.session_state.show_result = False
                st.rerun()
    
    with col3:
        if st.session_state.current_question < len(st.session_state.question_order) - 1:
            if st.button("Suivant ➡️"):
                st.session_state.current_question += 1
                st.session_state.show_result = False
                st.rerun()
        else:
            if st.button("🏁 Terminer le QCM"):
                st.session_state.submitted = True
                st.rerun()

# Afficher les résultats finaux
if st.session_state.submitted:
    st.success("QCM complété !")
    
    questions_to_check = [all_questions[idx] for idx in st.session_state.question_order]

    # Calculer le score et séparer correctes / incorrectes
    score = 0
    wrong_questions = []

    for i, q in enumerate(questions_to_check):
        user_answer = st.session_state.answers.get(q["id"], [])
        correct = is_answer_correct(q, user_answer)
        if correct:
            score += 1
        else:
            wrong_questions.append((i + 1, q, user_answer))

    st.metric("Score", f"{score}/{len(st.session_state.question_order)}")

    # Recap uniquement les questions ratées
    if wrong_questions:
        st.subheader(f"❌ Questions ratées ({len(wrong_questions)})")
        for num, q, user_answer in wrong_questions:
            with st.expander(f"Question {num} : {q['question']}"):
                st.write(f"**Votre réponse :** {', '.join(user_answer) if user_answer else 'Non répondu'}")
                st.write(f"**Bonne(s) réponse(s) :** {', '.join(q['correct'])}")
                st.error("❌ Incorrect !")
    else:
        st.balloons()
        st.success("🎉 Parfait ! Aucune erreur, t'es une légende.")

    if st.button("🔄 Recommencer"):
        st.session_state.current_question = 0
        st.session_state.answers = {}
        st.session_state.submitted = False
        st.session_state.show_result = False
        st.session_state.started = False
        st.session_state.num_questions_selected = None
        st.session_state.shuffled_options = {}
        st.rerun()