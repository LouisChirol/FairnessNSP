#!/usr/bin/env python3
"""
Streamlit web interface for FairnessNSP scheduling system.
"""

import streamlit as st
import pandas as pd
import os
import tempfile
from pathlib import Path
from nurse_scheduler import NurseScheduler
from caregiver_scheduler import CaregiverScheduler
from config_manager import get_nurse_config, get_caregiver_config


# Language translations
TRANSLATIONS = {
    'en': {
        'title': '🏥 FairnessNSP - Hospital Staff Scheduling',
        'description': 'This application helps create fair work schedules for hospital staff using Integer Linear Programming optimization. Select the staff type and configure the parameters below.',
        'nurses_tab': '👩‍⚕️ Nurses',
        'caregivers_tab': '👨‍⚕️ Caregivers',
        'nurse_header': 'Nurse Scheduling Configuration',
        'caregiver_header': 'Caregiver Scheduling Configuration',
        'general_params': 'General Parameters',
        'staffing_req': 'Staffing Requirements',
        'weekdays': 'Weekdays:',
        'weekends': 'Weekends:',
        'nb_nurses': 'Number of Nurses',
        'nb_caregivers': 'Number of Caregivers',
        'nb_weeks': 'Number of Weeks',
        'nb_shifts': 'Number of Shifts',
        'nb_part_time_nurses': 'Number of Part-time Nurses',
        'nb_part_time_caregivers': 'Number of Part-time Caregivers',
        'morning_week': 'Morning Shift (Weekdays)',
        'evening_week': 'Evening Shift (Weekdays)',
        'day_week': 'Day Shift (Weekdays)',
        'morning_weekend': 'Morning Shift (Weekends)',
        'evening_weekend': 'Evening Shift (Weekends)',
        'day_weekend': 'Day Shift (Weekends)',
        'generate_nurse': '🚀 Generate Nurse Schedule',
        'generate_caregiver': '🚀 Generate Caregiver Schedule',
        'optimizing_nurse': 'Optimizing nurse schedule...',
        'optimizing_caregiver': 'Optimizing caregiver schedule...',
        'success_nurse': '✅ Nurse schedule generated successfully!',
        'success_caregiver': '✅ Caregiver schedule generated successfully!',
        'status': 'Status',
        'objective_value': 'Objective Value',
        'output_file': 'Output File',
        'download_nurse': '📥 Download Nurse Schedule (Excel)',
        'download_caregiver': '📥 Download Caregiver Schedule (Excel)',
        'failed_generate': '❌ Failed to generate schedule. Please check the parameters.',
        'caregiver_constraints': 'Caregiver Constraints',
        'caregiver_info': '**Caregiver-specific constraints:**\n- Weekdays: 3 morning, 2 evening, 0 day shifts\n- Weekends: 4 total shifts (1-2 morning, 1-2 evening, 0 day)\n- These constraints are hardcoded based on hospital requirements',
        'footer_text': 'FairnessNSP - Hospital Staff Scheduling with Fairness Constraints\nBuilt with Streamlit, PuLP, and Python',
        'language_button': '🇫🇷 Français',
        'help_nurses': 'Total number of nurses (full-time + part-time)',
        'help_weeks': 'Number of weeks to schedule',
        'help_shifts': 'Number of different shift types (morning, evening, etc.)',
        'help_part_time': 'Number of nurses working part-time (80% workload)',
        'help_morning_week': 'Minimum nurses required for morning shift on weekdays',
        'help_evening_week': 'Minimum nurses required for evening shift on weekdays',
        'help_day_week': 'Minimum nurses required for day shift on weekdays',
        'help_morning_weekend': 'Minimum nurses required for morning shift on weekends',
        'help_evening_weekend': 'Minimum nurses required for evening shift on weekends',
        'help_day_weekend': 'Minimum nurses required for day shift on weekends',
        'help_caregivers': 'Total number of caregivers (full-time + part-time)',
        'help_part_time_caregivers': 'Number of caregivers working part-time (80% workload)'
    },
    'fr': {
        'title': '🏥 FairnessNSP - Planification du Personnel Hospitalier',
        'description': 'Cette application aide à créer des plannings équitables pour le personnel hospitalier en utilisant l\'optimisation par programmation linéaire en nombres entiers. Sélectionnez le type de personnel et configurez les paramètres ci-dessous.',
        'nurses_tab': '👩‍⚕️ Infirmiers',
        'caregivers_tab': '👨‍⚕️ Aides-soignants',
        'nurse_header': 'Configuration de la Planification des Infirmiers',
        'caregiver_header': 'Configuration de la Planification des Aides-soignants',
        'general_params': 'Paramètres Généraux',
        'staffing_req': 'Besoins en Personnel',
        'weekdays': 'Jours de semaine :',
        'weekends': 'Weekends :',
        'nb_nurses': 'Nombre d\'Infirmiers',
        'nb_caregivers': 'Nombre d\'Aides-soignants',
        'nb_weeks': 'Nombre de Semaines',
        'nb_shifts': 'Nombre d\'Équipes',
        'nb_part_time_nurses': 'Nombre d\'Infirmiers à Temps Partiel',
        'nb_part_time_caregivers': 'Nombre d\'Aides-soignants à Temps Partiel',
        'morning_week': 'Équipe du Matin (Semaine)',
        'evening_week': 'Équipe du Soir (Semaine)',
        'day_week': 'Équipe de Jour (Semaine)',
        'morning_weekend': 'Équipe du Matin (Weekend)',
        'evening_weekend': 'Équipe du Soir (Weekend)',
        'day_weekend': 'Équipe de Jour (Weekend)',
        'generate_nurse': '🚀 Générer le Planning des Infirmiers',
        'generate_caregiver': '🚀 Générer le Planning des Aides-soignants',
        'optimizing_nurse': 'Optimisation du planning des infirmiers...',
        'optimizing_caregiver': 'Optimisation du planning des aides-soignants...',
        'success_nurse': '✅ Planning des infirmiers généré avec succès !',
        'success_caregiver': '✅ Planning des aides-soignants généré avec succès !',
        'status': 'Statut',
        'objective_value': 'Valeur Objectif',
        'output_file': 'Fichier de Sortie',
        'download_nurse': '📥 Télécharger le Planning des Infirmiers (Excel)',
        'download_caregiver': '📥 Télécharger le Planning des Aides-soignants (Excel)',
        'failed_generate': '❌ Échec de la génération du planning. Veuillez vérifier les paramètres.',
        'caregiver_constraints': 'Contraintes des Aides-soignants',
        'caregiver_info': '**Contraintes spécifiques aux aides-soignants :**\n- Semaine : 3 matin, 2 soir, 0 jour\n- Weekends : 4 équipes total (1-2 matin, 1-2 soir, 0 jour)\n- Ces contraintes sont codées en dur selon les exigences hospitalières',
        'footer_text': 'FairnessNSP - Planification du Personnel Hospitalier avec Contraintes d\'Équité\nDéveloppé avec Streamlit, PuLP et Python',
        'language_button': '🇺🇸 English',
        'help_nurses': 'Nombre total d\'infirmiers (temps plein + temps partiel)',
        'help_weeks': 'Nombre de semaines à planifier',
        'help_shifts': 'Nombre de types d\'équipes différents (matin, soir, etc.)',
        'help_part_time': 'Nombre d\'infirmiers travaillant à temps partiel (80% de charge)',
        'help_morning_week': 'Nombre minimum d\'infirmiers requis pour l\'équipe du matin en semaine',
        'help_evening_week': 'Nombre minimum d\'infirmiers requis pour l\'équipe du soir en semaine',
        'help_day_week': 'Nombre minimum d\'infirmiers requis pour l\'équipe de jour en semaine',
        'help_morning_weekend': 'Nombre minimum d\'infirmiers requis pour l\'équipe du matin le weekend',
        'help_evening_weekend': 'Nombre minimum d\'infirmiers requis pour l\'équipe du soir le weekend',
        'help_day_weekend': 'Nombre minimum d\'infirmiers requis pour l\'équipe de jour le weekend',
        'help_caregivers': 'Nombre total d\'aides-soignants (temps plein + temps partiel)',
        'help_part_time_caregivers': 'Nombre d\'aides-soignants travaillant à temps partiel (80% de charge)'
    }
}


def get_text(key):
    """Get translated text based on current language."""
    lang = st.session_state.get('language', 'en')
    return TRANSLATIONS[lang].get(key, key)


def create_nurse_config_from_form():
    """Create nurse configuration from form inputs."""
    return {
        'I': range(1, st.session_state.nb_agents + 1),
        'J': range(1, st.session_state.nb_weeks * 6 + 1),
        'K': range(1, st.session_state.nb_shifts * 2 + 1),
        'nb_shifts': st.session_state.nb_shifts,
        'nb_weeks': st.session_state.nb_weeks,
        'part_time_I': range(1, st.session_state.nb_part_time_agents + 1),
        'full_time_I': [i for i in range(1, st.session_state.nb_agents + 1) 
                       if i > st.session_state.nb_part_time_agents],
        'staffing_constraints_week': [
            st.session_state.morning_week,
            st.session_state.evening_week,
            st.session_state.day_week
        ],
        'staffing_constraints_weekend': [
            st.session_state.morning_weekend,
            st.session_state.evening_weekend,
            st.session_state.day_weekend
        ],
        'dest_file': "nurses_schedule.xlsx"
    }


def create_caregiver_config_from_form():
    """Create caregiver configuration from form inputs."""
    return {
        'I': range(1, st.session_state.nb_agents + 1),
        'J': range(1, st.session_state.nb_weeks * 6 + 1),
        'K': range(1, st.session_state.nb_shifts * 2 + 1),
        'nb_shifts': st.session_state.nb_shifts,
        'nb_weeks': st.session_state.nb_weeks,
        'part_time_I': range(1, st.session_state.nb_part_time_agents + 1),
        'full_time_I': [i for i in range(1, st.session_state.nb_agents + 1) 
                       if i > st.session_state.nb_part_time_agents],
        'dest_file': "caregivers_schedule.xlsx"
    }


def run_scheduler(agent_type):
    """Run the scheduler for the specified agent type."""
    try:
        if agent_type == "Nurses":
            config = create_nurse_config_from_form()
            scheduler = NurseScheduler(config)
        else:  # Caregivers
            config = create_caregiver_config_from_form()
            scheduler = CaregiverScheduler(config)
        
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            config['dest_file'] = tmp_file.name
        
        # Run the scheduler
        prob, x = scheduler.build_model()
        
        # Solve
        prob.solve()
        
        # Export
        variable_names = [f"x{i},{j},{k}" for i in config['I'] for j in config['J'] for k in config['K']]
        values = [x[i, j, k].value() for i in config['I'] for j in config['J'] for k in config['K']]
        
        os.makedirs("output", exist_ok=True)
        dest_path = os.path.join("output", config['dest_file'])
        
        from excel_export import export_schedule
        export_schedule(values, variable_names, config['I'], config['J'], config['K'], 
                       config['part_time_I'], config['nb_shifts'], dest_path)
        
        return dest_path, prob.status, prob.objective.value()
        
    except Exception as e:
        st.error(f"Error during scheduling: {str(e)}")
        return None, None, None


def main():
    st.set_page_config(
        page_title="FairnessNSP - Hospital Scheduling",
        page_icon="🏥",
        layout="wide"
    )
    
    # Initialize language
    if 'language' not in st.session_state:
        st.session_state.language = 'en'
    
    # Header with title and language toggle
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.title(get_text('title'))
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        if st.button(get_text('language_button'), key="lang_button"):
            st.session_state.language = 'fr' if st.session_state.language == 'en' else 'en'
            st.rerun()
    
    st.markdown(get_text('description'))
    
    # Initialize session state
    if 'nb_agents' not in st.session_state:
        st.session_state.nb_agents = 11
    if 'nb_weeks' not in st.session_state:
        st.session_state.nb_weeks = 10
    if 'nb_shifts' not in st.session_state:
        st.session_state.nb_shifts = 3
    if 'nb_part_time_agents' not in st.session_state:
        st.session_state.nb_part_time_agents = 3
    
    # Create tabs
    tab1, tab2 = st.tabs([get_text('nurses_tab'), get_text('caregivers_tab')])
    
    with tab1:
        st.header(get_text('nurse_header'))
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(get_text('general_params'))
            st.session_state.nb_agents = st.number_input(
                get_text('nb_nurses'), 
                min_value=1, 
                max_value=50, 
                value=st.session_state.nb_agents,
                help=get_text('help_nurses')
            )
            
            st.session_state.nb_weeks = st.number_input(
                get_text('nb_weeks'), 
                min_value=1, 
                max_value=52, 
                value=st.session_state.nb_weeks,
                help=get_text('help_weeks')
            )
            
            st.session_state.nb_shifts = st.number_input(
                get_text('nb_shifts'), 
                min_value=1, 
                max_value=5, 
                value=st.session_state.nb_shifts,
                help=get_text('help_shifts')
            )
            
            st.session_state.nb_part_time_agents = st.number_input(
                get_text('nb_part_time_nurses'), 
                min_value=0, 
                max_value=st.session_state.nb_agents, 
                value=st.session_state.nb_part_time_agents,
                help=get_text('help_part_time')
            )
        
        with col2:
            st.subheader(get_text('staffing_req'))
            st.markdown(f"**{get_text('weekdays')}**")
            st.session_state.morning_week = st.number_input(
                get_text('morning_week'), 
                min_value=0, 
                max_value=20, 
                value=3,
                help=get_text('help_morning_week')
            )
            
            st.session_state.evening_week = st.number_input(
                get_text('evening_week'), 
                min_value=0, 
                max_value=20, 
                value=2,
                help=get_text('help_evening_week')
            )
            
            st.session_state.day_week = st.number_input(
                get_text('day_week'), 
                min_value=0, 
                max_value=20, 
                value=1,
                help=get_text('help_day_week')
            )
            
            st.markdown(f"**{get_text('weekends')}**")
            st.session_state.morning_weekend = st.number_input(
                get_text('morning_weekend'), 
                min_value=0, 
                max_value=20, 
                value=3,
                help=get_text('help_morning_weekend')
            )
            
            st.session_state.evening_weekend = st.number_input(
                get_text('evening_weekend'), 
                min_value=0, 
                max_value=20, 
                value=2,
                help=get_text('help_evening_weekend')
            )
            
            st.session_state.day_weekend = st.number_input(
                get_text('day_weekend'), 
                min_value=0, 
                max_value=20, 
                value=0,
                help=get_text('help_day_weekend')
            )
        
        # Run button
        if st.button(get_text('generate_nurse'), type="primary"):
            with st.spinner(get_text('optimizing_nurse')):
                output_path, status, objective = run_scheduler("Nurses")
                
                if output_path and os.path.exists(output_path):
                    st.success(get_text('success_nurse'))
                    
                    # Display results
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(get_text('status'), status)
                    with col2:
                        st.metric(get_text('objective_value'), f"{objective:.1f}")
                    with col3:
                        st.metric(get_text('output_file'), "nurses_schedule.xlsx")
                    
                    # Download button
                    with open(output_path, "rb") as file:
                        st.download_button(
                            label=get_text('download_nurse'),
                            data=file.read(),
                            file_name="nurses_schedule.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.error(get_text('failed_generate'))
    
    with tab2:
        st.header(get_text('caregiver_header'))
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(get_text('general_params'))
            st.session_state.nb_agents = st.number_input(
                get_text('nb_caregivers'), 
                min_value=1, 
                max_value=50, 
                value=9,
                key="caregiver_agents",
                help=get_text('help_caregivers')
            )
            
            st.session_state.nb_weeks = st.number_input(
                get_text('nb_weeks'), 
                min_value=1, 
                max_value=52, 
                value=10,
                key="caregiver_weeks",
                help=get_text('help_weeks')
            )
            
            st.session_state.nb_shifts = st.number_input(
                get_text('nb_shifts'), 
                min_value=1, 
                max_value=5, 
                value=3,
                key="caregiver_shifts",
                help=get_text('help_shifts')
            )
            
            st.session_state.nb_part_time_agents = st.number_input(
                get_text('nb_part_time_caregivers'), 
                min_value=0, 
                max_value=st.session_state.nb_agents, 
                value=1,
                key="caregiver_part_time",
                help=get_text('help_part_time_caregivers')
            )
        
        with col2:
            st.subheader(get_text('caregiver_constraints'))
            st.info(get_text('caregiver_info'))
        
        # Run button
        if st.button(get_text('generate_caregiver'), type="primary"):
            with st.spinner(get_text('optimizing_caregiver')):
                output_path, status, objective = run_scheduler("Caregivers")
                
                if output_path and os.path.exists(output_path):
                    st.success(get_text('success_caregiver'))
                    
                    # Display results
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(get_text('status'), status)
                    with col2:
                        st.metric(get_text('objective_value'), f"{objective:.1f}")
                    with col3:
                        st.metric(get_text('output_file'), "caregivers_schedule.xlsx")
                    
                    # Download button
                    with open(output_path, "rb") as file:
                        st.download_button(
                            label=get_text('download_caregiver'),
                            data=file.read(),
                            file_name="caregivers_schedule.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.error(get_text('failed_generate'))
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: #666;'>
        <p>{get_text('footer_text')}</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main() 