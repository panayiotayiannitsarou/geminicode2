import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import random
import math # Θα χρειαστούμε τη συνάρτηση ceil (οροφή)

# ----------------------------------------------------
# Βοηθητικές Συναρτήσεις (από τον κώδικά σας, με πιθανές βελτιώσεις)
# ----------------------------------------------------

def is_mutual_friend(df, child1_name, child2_name):
    # Εξασφάλιση ότι οι τιμές είναι συμβολοσειρές και χειρισμός NaN
    f1_val = df.loc[df['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'] == child1_name, 'ΦΙΛΙΑ'].values
    f2_val = df.loc[df['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'] == child2_name, 'ΦΙΛΙΑ'].values

    f1 = str(f1_val[0]) if f1_val.size > 0 and pd.notna(f1_val[0]) else ""
    f2 = str(f2_val[0]) if f2_val.size > 0 and pd.notna(f2_val[0]) else ""

    friends1 = [f.strip() for f in f1.split(",") if f.strip()]
    friends2 = [f.strip() for f in f2.split(",") if f.strip()]

    return (child2_name in friends1) and (child1_name in friends2)

def has_conflict(df, child1_name, child2_name):
    # Εξασφάλιση ότι οι τιμές είναι συμβολοσειρές και χειρισμός NaN
    c1_val = df.loc[df['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'] == child1_name, 'ΣΥΓΚΡΟΥΣΗ'].values
    c2_val = df.loc[df['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'] == child2_name, 'ΣΥΓΚΡΟΥΣΗ'].values

    c1 = str(c1_val[0]) if c1_val.size > 0 and pd.notna(c1_val[0]) else ""
    c2 = str(c2_val[0]) if c2_val.size > 0 and pd.notna(c2_val[0]) else ""

    conflicts1 = [c.strip() for c in c1.split(",") if c.strip()]
    conflicts2 = [c.strip() for c in c2.split(",") if c.strip()]

    return (child2_name in conflicts1) or (child1_name in conflicts2)

# Ενημερωμένη συνάρτηση τοποθέτησης για να κρατάει και στατιστικά
def τοποθέτηση(df_students, τμηματα_dict, class_stats_dict, μαθητης_name, τμημα_name, κλειδωμα=True):
    # Εύρεση της γραμμής του μαθητή
    idx = df_students.index[df_students['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'] == μαθητης_name].tolist()
    if not idx:
        st.warning(f"Προσοχή: Μαθητής '{μαθητης_name}' δεν βρέθηκε στο DataFrame.")
        return

    idx = idx[0]
    
    # Ενημέρωση DataFrame
    df_students.at[idx, 'ΤΜΗΜΑ'] = τμημα_name
    df_students.at[idx, 'ΚΛΕΙΔΩΜΕΝΟΣ'] = κλειδωμα

    # Προσθήκη μαθητή στο λεξικό τμημάτων
    τμηματα_dict[τμημα_name].append(μαθητης_name)

    # Ενημέρωση στατιστικών τμήματος
    if τμημα_name not in class_stats_dict:
        class_stats_dict[τμημα_name] = initialize_class_stats() # Βοηθητική συνάρτηση
    
    student_row = df_students.loc[idx] # Παίρνουμε την τρέχουσα σειρά του μαθητή

    # Ενημέρωση πλήθους
    class_stats_dict[τμημα_name]['count'] += 1

    # Ενημέρωση χαρακτηριστικών
    # Λίστα με τα χαρακτηριστικά που παρακολουθούμε (εκτός από ΦΙΛΙΑ, ΣΥΓΚΡΟΥΣΗ, ΟΝΟΜΑΤΕΠΩΝΥΜΟ, ΤΜΗΜΑ, ΚΛΕΙΔΩΜΕΝΟΣ)
    characteristics = ['ΦΥΛΟ', 'ΠΑΙΔΙ ΕΚΠΑΙΔΕΥΤΙΚΟΥ', 'ΖΩΗΡΟΣ', 'ΙΔΙΑΙΤΕΡΟΤΗΤΑ', 'ΚΑΛΗ ΓΝΩΣΗ ΕΛΛΗΝΙΚΩΝ', 'ΙΚΑΝΟΠΟΙΗΤ']
    
    for char in characteristics:
        if char == 'ΦΥΛΟ':
            if student_row[char] == 'Κ':
                class_stats_dict[τμημα_name]['ΦΥΛΟ_Κ'] += 1
            elif student_row[char] == 'Α':
                class_stats_dict[τμημα_name]['ΦΥΛΟ_Α'] += 1
        elif student_row[char] == 'Ν': # Για χαρακτηριστικά Ν/Ο
            class_stats_dict[τμημα_name][f'{char}_Ν'] += 1


# Βοηθητική συνάρτηση για την αρχικοποίηση των στατιστικών τμήματος
def initialize_class_stats():
    stats = {'count': 0, 'ΦΥΛΟ_Κ': 0, 'ΦΥΛΟ_Α': 0}
    characteristics_N_O = ['ΠΑΙΔΙ ΕΚΠΑΙΔΕΥΤΙΚΟΥ', 'ΖΩΗΡΟΣ', 'ΙΔΙΑΙΤΕΡΟΤΗΤΑ', 'ΚΑΛΗ ΓΝΩΣΗ ΕΛΛΗΝΙΚΩΝ', 'ΙΚΑΝΟΠΟΙΗΤ']
    for char in characteristics_N_O:
        stats[f'{char}_Ν'] = 0
    return stats

# Νέα βοηθητική συνάρτηση για τον έλεγχο τοποθέτησης
def can_place(df_students, student_row, target_class_name, τμηματα_dict, class_stats_dict, max_students_per_class, all_class_names):
    # 1. Έλεγχος μεγέθους τμήματος (να μην υπερβαίνει το max_students_per_class)
    if class_stats_dict[target_class_name]['count'] >= max_students_per_class:
        return False, "Το τμήμα είναι πλήρες."
    
    # 2. Έλεγχος διαφοράς πληθυσμού - Πιο αυστηρός έλεγχος για να διατηρηθεί η ισορροπία
    # Υποθετικό πλήθος μαθητών αν τοποθετηθεί ο μαθητής
    hypothetical_counts = {cls: stats['count'] for cls, stats in class_stats_dict.items()}
    hypothetical_counts[target_class_name] += 1
    
    # Εξαιρούμε τμήματα που είναι ακόμα άδεια από τον έλεγχο min/max για να επιτρέψουμε την αρχική τοποθέτηση
    non_empty_counts = [count for count in hypothetical_counts.values() if count > 0]
    
    if non_empty_counts: # Μόνο αν υπάρχουν μη-άδεια τμήματα
        min_count_non_empty = min(non_empty_counts)
        max_count_non_empty = max(non_empty_counts)
        
        if max_count_non_empty - min_count_non_empty > 1:
            # Επιτρέπουμε μόνο αν το τμήμα στο οποίο προσπαθούμε να τοποθετήσουμε
            # δεν είναι το μεγαλύτερο και η διαφορά δεν ξεπερνάει το 1
            if hypothetical_counts[target_class_name] > min_count_non_empty + 1:
                return False, "Η τοποθέτηση θα χαλάσει την ισορροπία πληθυσμού (>1)."

    # 3. Έλεγχος συγκρούσεων με ήδη τοποθετημένους μαθητές στο τμήμα
    for placed_student_name in τμηματα_dict[target_class_name]:
        if has_conflict(df_students, student_row['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'], placed_student_name):
            return False, f"Σύγκρουση με μαθητή '{placed_student_name}' στο τμήμα."
    
    return True, "Μπορεί να τοποθετηθεί."


# ----------------------------------------------------
# Κύρια Συνάρτηση Κατανομής Μαθητών
# ----------------------------------------------------

def πλήρης_κατανομή(df_initial, num_classes_input, max_students_per_class_input):
    df = df_initial.copy() # Δουλεύουμε σε αντίγραφο του DataFrame

    # Αρχικοποίηση στηλών αν δεν υπάρχουν
    if 'ΤΜΗΜΑ' not in df.columns:
        df['ΤΜΗΜΑ'] = None
    if 'ΚΛΕΙΔΩΜΕΝΟΣ' not in df.columns:
        df['ΚΛΕΙΔΩΜΕΝΟΣ'] = False

    num_students = len(df)
    
    # 1. Βήμα: Ισορροπία Πληθυσμού - Έλεγχος ελάχιστου αριθμού τμημάτων
    min_required_classes = math.ceil(num_students / max_students_per_class_input)
    if num_classes_input < min_required_classes:
        st.error(f"Ο αριθμός τμημάτων ({num_classes_input}) είναι πολύ μικρός για τους {num_students} μαθητές. Χρειάζονται τουλάχιστον {min_required_classes} τμήματα με μέγιστο {max_students_per_class_input} μαθητές ανά τμήμα.")
        return None # Επιστρέφουμε None ή κάποια ένδειξη σφάλματος

    # Αρχικοποίηση δομών δεδομένων
    τμηματα = {f'Τμήμα {i+1}': [] for i in range(num_classes_input)}
    class_stats = {f'Τμήμα {i+1}': initialize_class_stats() for i in range(num_classes_input)}
    all_class_names = list(τμηματα.keys()) # Λίστα με ονόματα τμημάτων

    # Σημείωση: Από εδώ και πέρα, θα υλοποιηθούν τα Βήματα 2-8 με τη σειρά.
    # Αυτό το πρώτο κομμάτι είναι η προετοιμασία.

    st.write("Ξεκινάει η προηγμένη κατανομή...")

    # Δημιουργία λίστας μη κλειδωμένων μαθητών για επεξεργασία
    unlocked_students_df = df[~df['ΚΛΕΙΔΩΜΕΝΟΣ']].copy().sample(frac=1, random_state=42).reset_index(drop=True) # Ανακάτεμα για τυχαιότητα στην επιλογή

    # ----- Βήμα 2: Παιδιά Εκπαιδευτικών -----
    st.subheader("Βήμα 2: Τοποθέτηση Παιδιών Εκπαιδευτικών")
    teacher_children = unlocked_students_df[unlocked_students_df['ΠΑΙΔΙ ΕΚΠΑΙΔΕΥΤΙΚΟΥ'] == 'Ν'].copy()
    
    # Προσπάθεια να τοποθετήσουμε ένα παιδί εκπαιδευτικού ανά τμήμα, αν είναι εφικτό
    current_class_idx = 0
    for idx, student_row in teacher_children.iterrows():
        student_name = student_row['ΟΝΟΜΑΤΕΠΩΝΥΜΟ']
        
        # Ελέγχουμε αν ο μαθητής έχει ήδη τοποθετηθεί (πχ. αν υπάρχει σε λίστα κλειδωμένων ή στο df)
        if df.loc[df['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'] == student_name, 'ΚΛΕΙΔΩΜΕΝΟΣ'].iloc[0]:
            continue # Αυτός ο μαθητής έχει ήδη τοποθετηθεί σε προηγούμενο υπο-βήμα ή λόγω φιλίας

        # Βρες ένα διαθέσιμο τμήμα, ξεκινώντας από το current_class_idx
        start_class_idx = current_class_idx
        placed_in_step = False
        while True:
            target_class_name = all_class_names[current_class_idx]
            
            # Ελέγχουμε αν το τμήμα έχει ήδη παιδί εκπαιδευτικού
            if class_stats[target_class_name]['ΠΑΙΔΙ ΕΚΠΑΙΔΕΥΤΙΚΟΥ_Ν'] == 0:
                is_valid, msg = can_place(df, student_row, target_class_name, τμηματα, class_stats, max_students_per_class, all_class_names)
                if is_valid:
                    τοποθέτηση(df, τμηματα, class_stats, student_name, target_class_name, κλειδωμα=True)
                    st.info(f"Τοποθετήθηκε ο/η μαθητής/τρια '{student_name}' (Παιδί Εκπαιδευτικού) στο {target_class_name}.")
                    placed_in_step = True
                    break
            
            current_class_idx = (current_class_idx + 1) % num_classes_input
            if current_class_idx == start_class_idx: # Έχουμε κάνει έναν πλήρη κύκλο
                break # Δεν βρέθηκε τμήμα χωρίς παιδί εκπαιδευτικού ή πλήρες

        if not placed_in_step: # Αν δεν τοποθετήθηκε ακόμα, προσπάθησε σε οποιοδήποτε διαθέσιμο τμήμα
            for class_name in all_class_names:
                is_valid, msg = can_place(df, student_row, class_name, τμηματα, class_stats, max_students_per_class, all_class_names)
                if is_valid:
                    τοποθέτηση(df, τμηματα, class_stats, student_name, class_name, κλειδωμα=True)
                    st.info(f"Τοποθετήθηκε ο/η μαθητής/τρια '{student_name}' (Παιδί Εκπαιδευτικού) στο {class_name} (Αναπληρωματικό).")
                    placed_in_step = True
                    break
        
        # Ενημέρωση της λίστας των μη κλειδωμένων μαθητών αν τοποθετήθηκε
        if placed_in_step:
            unlocked_students_df = unlocked_students_df[unlocked_students_df['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'] != student_name]

    # Χειρισμός φιλίας μεταξύ παιδιών εκπαιδευτικών και ισορροπία φύλου
    # Αυτό είναι πιο σύνθετο και θα γίνει σε επόμενο βήμα, καθώς προϋποθέτει ζευγαρώματα/τριάδες
    # Για τώρα, απλά τοποθετούμε μεμονωμένα τα παιδιά εκπαιδευτικών.
    # Η λογική για "Αν υπάρχει αμοιβαία φιλία με άλλο παιδί εκπαιδευτικού, τοποθετούνται μαζί μόνο αν ο συνολικός αριθμός παιδιών εκπαιδευτικών είναι μεγαλύτερος από τον αριθμό των τμημάτων."
    # και "Προτιμάται ισορροπία φύλου" θα αντιμετωπιστεί στην επόμενη φάση του αλγορίθμου, ίσως στο Βήμα 5 ή σε ειδικό helper.

    # ----- Βήμα 3: Ζωηροί Μαθητές -----
    # Κωδικοποίηση για Βήμα 3 θα ακολουθήσει

    # ----- Βήμα 4: Παιδιά με Ιδιαιτερότητες -----
    # Κωδικοποίηση για Βήμα 4 θα ακολουθήσει

    # ----- Βήμα 5: Φίλοι Παιδιών που Τοποθετήθηκαν -----
    # Κωδικοποίηση για Βήμα 5 θα ακολουθήσει

    # ----- Βήμα 6: Φιλικές Ομάδες ανά Γνώση Ελληνικών -----
    # Κωδικοποίηση για Βήμα 6 θα ακολουθήσει

    # ----- Βήμα 7: Υπόλοιποι Μαθητές Χωρίς Φιλίες -----
    # Κωδικοποίηση για Βήμα 7 θα ακολουθήσει

    # ----- Βήμα 8: Έλεγχος Ποιοτικών Χαρακτηριστικών & Διορθώσεις -----
    # Κωδικοποίηση για Βήμα 8 θα ακολουθήσει


    return df

# ----------------------------------------------------
# Λοιπές συναρτήσεις (ίδιες με αυτές που παρείχατε)
# ----------------------------------------------------

def create_excel_file(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Κατανομή')
    return output.getvalue()

def plot_distribution(df, column, title):
    fig, ax = plt.subplots(figsize=(10, 6)) # Καλύτερο μέγεθος γραφήματος
    
    # Ensure all categories are present, even if counts are 0
    # For 'ΦΥΛΟ', use 'Κ' and 'Α'
    if column == 'ΦΥΛΟ':
        categories = ['Κ', 'Α']
    else: # For 'Ν'/'Ο' columns
        categories = ['Ν', 'Ο']

    # Unstacking might create NaNs if a category is missing in a group
    grouped_data = df.groupby(['ΤΜΗΜΑ', column]).size().unstack(fill_value=0)
    
    # Reindex to ensure all categories are in the plot, even if they have 0 count
    for cat in categories:
        if cat not in grouped_data.columns:
            grouped_data[cat] = 0

    # Ensure column order for consistent plotting
    grouped_data = grouped_data[categories]
    
    grouped_data.plot(kind='bar', stacked=True, ax=ax)
    
    ax.set_title(title)
    ax.set_ylabel('Αριθμός Μαθητών')
    ax.set_xlabel('Τμήμα')
    plt.xticks(rotation=45, ha='right') # Περιστροφή labels
    plt.tight_layout() # Προσαρμογή layout
    st.pyplot(fig)

# ----------------------------------------------------
# Κύριο μέρος εφαρμογής Streamlit
# ----------------------------------------------------

# Έλεγχος Κωδικού Πρόσβασης
st.sidebar.title("🔐 Κωδικός Πρόσβασης")
password = st.sidebar.text_input("Εισάγετε τον κωδικό:", type="password")
if password != "katanomi2025":
    st.warning("Παρακαλώ εισάγετε έγκυρο κωδικό για πρόσβαση στην εφαρμογή.")
    st.stop()

# Ενεργοποίηση/Απενεργοποίηση Εφαρμογής
enable_app = st.sidebar.checkbox("✅ Ενεργοποίηση Εφαρμογής", value=True)
if not enable_app:
    st.info("✋ Η εφαρμογή είναι προσωρινά απενεργοποιημένη.")
    st.stop()


st.title("📊 Ψηφιακή Κατανομή Μαθητών Α' Δημοτικού")

uploaded_file = st.file_uploader("⬆️ Εισαγωγή Excel αρχείου μαθητών", type="xlsx")

df_students = None # Ορίζουμε το df_students εκτός του if για να είναι πάντα διαθέσιμο

if uploaded_file is not None:
    df_students = pd.read_excel(uploaded_file)
    st.success("✅ Το αρχείο φορτώθηκε επιτυχώς!")

    # Εμφάνιση των πρώτων γραμμών του DataFrame για επιβεβαίωση
    st.subheader("Προεπισκόπηση Δεδομένων:")
    st.dataframe(df_students.head())

    # Εισαγωγές χρήστη για αριθμό τμημάτων και μέγιστο πλήθος
    st.sidebar.subheader("Ρυθμίσεις Κατανομής")
    num_classes_input = st.sidebar.number_input("Αριθμός Τμημάτων:", min_value=1, value=3, step=1)
    max_students_per_class_input = st.sidebar.number_input("Μέγιστος αριθμός μαθητών ανά τμήμα:", min_value=10, max_value=30, value=25, step=1)


    if st.button("▶️ Εκτέλεση Κατανομής Μαθητών"):
        # Κλήση της ενημερωμένης συνάρτησης κατανομής με τις εισόδους του χρήστη
        df_katanomi = πλήρης_κατανομή(df_students.copy(), num_classes_input, max_students_per_class_input)
        if df_katanomi is not None: # Ελέγχουμε αν η κατανομή ήταν επιτυχής
            st.session_state["df_katanomi"] = df_katanomi
            st.success("✅ Ολοκληρώθηκε η κατανομή μαθητών!")
        else:
            # Η πλήρης_κατανομή έχει ήδη εμφανίσει μήνυμα λάθους
            pass

# Εμφάνιση αποτελεσμάτων μόνο αν υπάρχει κατανομή στο session_state
if "df_katanomi" in st.session_state and st.session_state["df_katanomi"] is not None:
    df_result = st.session_state["df_katanomi"]

    st.subheader("📊 Αποτελέσματα Κατανομής")
    st.dataframe(df_result) # Εμφανίζει ολόκληρο το DataFrame με τα τμήματα

    if st.button("⬇️ Λήψη Excel με Κατανομή"):
        excel_bytes = create_excel_file(df_result)
        st.download_button(
            label="⬇️ Κατέβασε το αρχείο Excel",
            data=excel_bytes,
            file_name="katanomi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.subheader("📊 Πίνακας Στατιστικών Κατανομής")
    # Χρησιμοποιούμε το df_result για τα στατιστικά
    if 'ΤΜΗΜΑ' in df_result.columns and not df_result['ΤΜΗΜΑ'].isnull().all():
        characteristics_for_stats = ['ΦΥΛΟ', 'ΖΩΗΡΟΣ', 'ΙΔΙΑΙΤΕΡΟΤΗΤΑ', 'ΚΑΛΗ ΓΝΩΣΗ ΕΛΛΗΝΙΚΩΝ', 'ΠΑΙΔΙ ΕΚΠΑΙΔΕΥΤΙΚΟΥ', 'ΙΚΑΝΟΠΟΙΗΤ']
        
        # Μετατροπή "Ο" σε False και "Ν" σε True για αριθμητικό sum
        df_stats = df_result.copy()
        for col in characteristics_for_stats:
            if col != 'ΦΥΛΟ': # Το φύλο έχει 'Κ'/'Α', όχι 'Ν'/'Ο'
                df_stats[col] = df_stats[col].apply(lambda x: True if x == 'Ν' else False)

        # Ειδικός χειρισμός για το ΦΥΛΟ
        female_counts = df_stats[df_stats['ΦΥΛΟ'] == 'Κ'].groupby('ΤΜΗΜΑ').size().reindex(df_result['ΤΜΗΜΑ'].unique(), fill_value=0)
        male_counts = df_stats[df_stats['ΦΥΛΟ'] == 'Α'].groupby('ΤΜΗΜΑ').size().reindex(df_result['ΤΜΗΜΑ'].unique(), fill_value=0)

        stats_table = pd.DataFrame({
            'Σύνολο Μαθητών': df_result.groupby('ΤΜΗΜΑ').size().reindex(df_result['ΤΜΗΜΑ'].unique(), fill_value=0),
            'Κορίτσια': female_counts,
            'Αγόρια': male_counts,
        })
        
        for col in characteristics_for_stats:
            if col != 'ΦΥΛΟ':
                # Sum True (δηλαδή 'Ν' αρχικά)
                stats_table[f'{col} (Ναι)'] = df_stats.groupby('ΤΜΗΜΑ')[col].sum().reindex(df_result['ΤΜΗΜΑ'].unique(), fill_value=0)
        
        st.dataframe(stats_table)
    else:
        st.info("Δεν έχουν τοποθετηθεί μαθητές σε τμήματα ακόμα για στατιστικά.")

    st.subheader("📈 Ραβδογράμματα Κατανομής")
    επιλογη = st.radio("Επιλέξτε τύπο γραφήματος:", ["Συγκεντρωτικά", "Ξεχωριστά ανά κατηγορία"])

    plot_columns = ['ΦΥΛΟ', 'ΖΩΗΡΟΣ', 'ΙΔΙΑΙΤΕΡΟΤΗΤΑ', 'ΚΑΛΗ ΓΝΩΣΗ ΕΛΛΗΝΙΚΩΝ', 'ΠΑΙΔΙ ΕΚΠΑΙΔΕΥΤΙΚΟΥ', 'ΙΚΑΝΟΠΟΙΗΤ'] # Χρησιμοποιούμε ΙΚΑΝΟΠΟΙΗΤ
    plot_titles = {
        'ΦΥΛΟ': 'Κατανομή Φύλου',
        'ΖΩΗΡΟΣ': 'Κατανομή Ζωηρών Μαθητών',
        'ΙΔΙΑΙΤΕΡΟΤΗΤΑ': 'Κατανομή Ιδιαιτεροτήτων',
        'ΚΑΛΗ ΓΝΩΣΗ ΕΛΛΗΝΙΚΩΝ': 'Κατανομή Καλής Γνώσης Ελληνικών',
        'ΠΑΙΔΙ ΕΚΠΑΙΔΕΥΤΙΚΟΥ': 'Κατανομή Παιδιών Εκπαιδευτικών',
        'ΙΚΑΝΟΠΟΙΗΤ': 'Κατανομή Ικανοποιητικής Μαθησιακής Ικανότητας'
    }

    if επιλογη == "Συγκεντρωτικά":
        for col in plot_columns:
            if col in df_result.columns: # Έλεγχος αν υπάρχει η στήλη
                plot_distribution(df_result, col, plot_titles.get(col, f"Κατανομή βάσει {col}"))
            else:
                st.warning(f"Η στήλη '{col}' δεν βρέθηκε στο αρχείο σας για γραφήματα.")
    else: # Ξεχωριστά ανά κατηγορία
        for col in plot_columns:
            if col in df_result.columns: # Έλεγχος αν υπάρχει η στήλη
                plot_distribution(df_result, col, f"Κατανομή βάσει {col}")
            else:
                st.warning(f"Η στήλη '{col}' δεν βρέθηκε στο αρχείο σας για γραφήματα.")

# Δήλωση Πνευματικών Δικαιωμάτων
st.markdown("---")
st.markdown(
    """
    📌 **Νομική Δήλωση**: Η χρήση της εφαρμογής επιτρέπεται μόνο με ρητή γραπτή άδεια της δημιουργού, Παναγιώτας Γιαννιτσοπούλου.
    Όλα τα πνευματικά δικαιώματα ανήκουν στη Γιαννιτσοπούλου Παναγιώτα. Για άδεια χρήσης:
    [yiannitsoopanayiota.katanomi@gmail.com](mailto:yiannitsoopanayiota.katanomi@gmail.com)
    """
)
