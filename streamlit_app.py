#!/usr/bin/env python3
"""
Streamlit web interface for FairnessNSP scheduling system.
"""

import streamlit as st
import pandas as pd
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

from pulp import LpStatus
from nurse_scheduler import NurseScheduler
from caregiver_scheduler import CaregiverScheduler
from config_manager import get_nurse_config, get_caregiver_config
from constraint_schema import StaffingSpec
from llm_service import LLMConstraintParser
from custom_scheduler_executor import run_custom_schedule


# Language translations
TRANSLATIONS = {
    'en': {
        'title': '🏥 FairnessNSP - Hospital Staff Scheduling',
        'description': 'This application helps create fair work schedules for hospital staff using Integer Linear Programming optimization. Select the staff type and configure the parameters below.',
        'nurses_tab': '👩‍⚕️ Nurses',
        'caregivers_tab': '👨‍⚕️ Caregivers',
        'custom_tab': '⚙️ Custom',
        'nurse_header': 'Nurse Scheduling Configuration',
        'caregiver_header': 'Caregiver Scheduling Configuration',
        'custom_header': 'Custom Scheduling Configuration',
        'general_params': 'General Parameters',
        'staffing_req': 'Staffing Requirements',
        'custom_constraints': 'Custom Constraints',
        'weekdays': 'Weekdays:',
        'weekends': 'Weekends:',
        'nb_nurses': 'Number of Nurses',
        'nb_caregivers': 'Number of Caregivers',
        'nb_agents': 'Number of Agents',
        'nb_weeks': 'Number of Weeks',
        'nb_shifts': 'Number of Shifts',
        'nb_part_time_nurses': 'Number of Part-time Nurses',
        'nb_part_time_caregivers': 'Number of Part-time Caregivers',
        'nb_part_time_agents': 'Number of Part-time Agents',
        'morning_week': 'Morning Shift (Weekdays)',
        'evening_week': 'Evening Shift (Weekdays)',
        'day_week': 'Day Shift (Weekdays)',
        'morning_weekend': 'Morning Shift (Weekends)',
        'evening_weekend': 'Evening Shift (Weekends)',
        'day_weekend': 'Day Shift (Weekends)',
        'generate_nurse': '🚀 Generate Nurse Schedule',
        'generate_caregiver': '🚀 Generate Caregiver Schedule',
        'generate_custom': '🚀 Generate Custom Schedule',
        'optimizing_nurse': 'Optimizing nurse schedule...',
        'optimizing_caregiver': 'Optimizing caregiver schedule...',
        'optimizing_custom': 'Generating and optimizing custom schedule...',
        'success_nurse': '✅ Nurse schedule generated successfully!',
        'success_caregiver': '✅ Caregiver schedule generated successfully!',
        'success_custom': '✅ Custom schedule generated successfully!',
        'status': 'Status',
        'objective_value': 'Objective Value',
        'output_file': 'Output File',
        'download_nurse': '📥 Download Nurse Schedule (Excel)',
        'download_caregiver': '📥 Download Caregiver Schedule (Excel)',
        'download_custom': '📥 Download Custom Schedule (Excel)',
        'failed_generate': '❌ Failed to generate schedule. Please check the parameters.',
        'failed_generate_custom': '❌ Failed to generate custom schedule. Please check your constraints.',
        'caregiver_constraints': 'Caregiver Constraints',
        'caregiver_info': '**Caregiver-specific constraints:**\n- Weekdays: 3 morning, 2 evening, 0 day shifts\n- Weekends: 4 total shifts (1-2 morning, 1-2 evening, 0 day)\n- These constraints are hardcoded based on hospital requirements',
        'custom_info': '**Custom Scheduling:**\n- Define your own constraints in natural language\n- The AI will generate a custom optimization model\n- Supports any scheduling requirements you specify',
        'constraints_placeholder': 'Describe your scheduling constraints here...\n\nExample:\n- We need 2 agents on morning shift and 1 on evening shift every day\n- Agents cannot work more than 4 consecutive days\n- Part-time agents work 60% of the time\n- Weekend shifts require 1 extra agent',
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
        'help_part_time_caregivers': 'Number of caregivers working part-time (80% workload)',
        'help_custom_agents': 'Total number of agents (full-time + part-time)',
        'help_custom_part_time': 'Number of agents working part-time',
        'parse_constraints': 'Parse Constraints with AI',
        'parsing_constraints': 'Parsing your constraints with AI…',
        'confirm_and_run': 'Confirm and Run Optimization',
        'running_optimization': 'Running optimization…',
        'edit_constraints': 'Edit Constraints (start over)',
        'parsed_constraints_title': 'The AI understood your constraints as:',
        'parse_success': 'Constraints parsed successfully. Please review and confirm before optimizing.',
        'parse_failed': 'Could not parse constraints. Error: {}',
        'infeasible_warning': (
            'The solver could not find a valid schedule (status: {}). '
            'The constraints may be infeasible — for example, more staff required '
            'than available, or incompatible shift rules. '
            'Try reducing staffing minimums or increasing the number of agents.'
        ),
        'llm_notes': 'Note from AI (constraints it could not fully encode):',
        'no_api_key': (
            'No MISTRAL_API_KEY found. '
            'Please create a .env file with your API key. '
            'See .env.example for the format.'
        ),
        'constraints_label': 'Describe your scheduling constraints:',
        'constraints_help': 'Describe your scheduling requirements in natural language.',
        'constraints_empty': 'Please describe your scheduling constraints first.',
    },
    'fr': {
        'title': '🏥 FairnessNSP - Planification du Personnel Hospitalier',
        'description': 'Cette application aide à créer des plannings équitables pour le personnel hospitalier en utilisant l\'optimisation par programmation linéaire en nombres entiers. Sélectionnez le type de personnel et configurez les paramètres ci-dessous.',
        'nurses_tab': '👩‍⚕️ Infirmiers',
        'caregivers_tab': '👨‍⚕️ Aides-soignants',
        'custom_tab': '⚙️ Personnalisé',
        'nurse_header': 'Configuration de la Planification des Infirmiers',
        'caregiver_header': 'Configuration de la Planification des Aides-soignants',
        'custom_header': 'Configuration de Planification Personnalisée',
        'general_params': 'Paramètres Généraux',
        'staffing_req': 'Besoins en Personnel',
        'custom_constraints': 'Contraintes Personnalisées',
        'weekdays': 'Jours de semaine :',
        'weekends': 'Weekends :',
        'nb_nurses': 'Nombre d\'Infirmiers',
        'nb_caregivers': 'Nombre d\'Aides-soignants',
        'nb_agents': 'Nombre d\'Agents',
        'nb_weeks': 'Nombre de Semaines',
        'nb_shifts': 'Nombre d\'Équipes',
        'nb_part_time_nurses': 'Nombre d\'Infirmiers à Temps Partiel',
        'nb_part_time_caregivers': 'Nombre d\'Aides-soignants à Temps Partiel',
        'nb_part_time_agents': 'Nombre d\'Agents à Temps Partiel',
        'morning_week': 'Équipe du Matin (Semaine)',
        'evening_week': 'Équipe du Soir (Semaine)',
        'day_week': 'Équipe de Jour (Semaine)',
        'morning_weekend': 'Équipe du Matin (Weekend)',
        'evening_weekend': 'Équipe du Soir (Weekend)',
        'day_weekend': 'Équipe de Jour (Weekend)',
        'generate_nurse': '🚀 Générer le Planning des Infirmiers',
        'generate_caregiver': '🚀 Générer le Planning des Aides-soignants',
        'generate_custom': '🚀 Générer le Planning Personnalisé',
        'optimizing_nurse': 'Optimisation du planning des infirmiers...',
        'optimizing_caregiver': 'Optimisation du planning des aides-soignants...',
        'optimizing_custom': 'Génération et optimisation du planning personnalisé...',
        'success_nurse': '✅ Planning des infirmiers généré avec succès !',
        'success_caregiver': '✅ Planning des aides-soignants généré avec succès !',
        'success_custom': '✅ Planning personnalisé généré avec succès !',
        'status': 'Statut',
        'objective_value': 'Valeur Objectif',
        'output_file': 'Fichier de Sortie',
        'download_nurse': '📥 Télécharger le Planning des Infirmiers (Excel)',
        'download_caregiver': '📥 Télécharger le Planning des Aides-soignants (Excel)',
        'download_custom': '📥 Télécharger le Planning Personnalisé (Excel)',
        'failed_generate': '❌ Échec de la génération du planning. Veuillez vérifier les paramètres.',
        'failed_generate_custom': '❌ Échec de la génération du planning personnalisé. Veuillez vérifier vos contraintes.',
        'caregiver_constraints': 'Contraintes des Aides-soignants',
        'caregiver_info': '**Contraintes spécifiques aux aides-soignants :**\n- Semaine : 3 matin, 2 soir, 0 jour\n- Weekends : 4 équipes total (1-2 matin, 1-2 soir, 0 jour)\n- Ces contraintes sont codées en dur selon les exigences hospitalières',
        'custom_info': '**Planification Personnalisée :**\n- Définissez vos propres contraintes en langage naturel\n- L\'IA générera un modèle d\'optimisation personnalisé\n- Prend en charge tous vos besoins de planification',
        'constraints_placeholder': 'Décrivez vos contraintes de planification ici...\n\nExemple :\n- Nous avons besoin de 2 agents en équipe du matin et 1 en équipe du soir chaque jour\n- Les agents ne peuvent pas travailler plus de 4 jours consécutifs\n- Les agents à temps partiel travaillent 60% du temps\n- Les équipes de weekend nécessitent 1 agent supplémentaire',
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
        'help_part_time_caregivers': 'Nombre d\'aides-soignants travaillant à temps partiel (80% de charge)',
        'help_custom_agents': 'Nombre total d\'agents (temps plein + temps partiel)',
        'help_custom_part_time': 'Nombre d\'agents travaillant à temps partiel',
        'parse_constraints': "Analyser les contraintes avec l'IA",
        'parsing_constraints': "Analyse de vos contraintes avec l'IA…",
        'confirm_and_run': "Confirmer et lancer l'optimisation",
        'running_optimization': "Optimisation en cours…",
        'edit_constraints': 'Modifier les contraintes (recommencer)',
        'parsed_constraints_title': "L'IA a compris vos contraintes ainsi :",
        'parse_success': 'Contraintes analysées. Veuillez vérifier et confirmer avant de lancer.',
        'parse_failed': "Impossible d'analyser les contraintes. Erreur : {}",
        'infeasible_warning': (
            'Le solveur n\'a pas trouvé de planning valide (statut : {}). '
            'Les contraintes sont peut-être infaisables — par exemple, plus d\'agents '
            'requis que disponibles ou règles incompatibles. '
            'Réduisez les minimums ou augmentez le nombre d\'agents.'
        ),
        'llm_notes': "Note de l'IA (contraintes qu'elle n'a pas pu encoder) :",
        'no_api_key': (
            'Clé MISTRAL_API_KEY introuvable. '
            'Créez un fichier .env avec votre clé. '
            'Voir .env.example pour le format.'
        ),
        'constraints_label': 'Décrivez vos contraintes de planification :',
        'constraints_help': 'Décrivez vos besoins en langage naturel.',
        'constraints_empty': 'Veuillez d\'abord décrire vos contraintes de planification.',
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


def parse_custom_constraints(
    user_constraints: str,
    basic_params: Dict[str, Any],
    lang: str = "en",
) -> tuple[Optional[StaffingSpec], Optional[str]]:
    """
    Step 1: Call the LLM to parse natural-language constraints into a StaffingSpec.
    Returns (spec, error_message); exactly one of them is always None.
    """
    try:
        parser = LLMConstraintParser()
        spec = parser.parse(user_constraints, basic_params, lang=lang)
        return spec, None
    except EnvironmentError:
        return None, get_text('no_api_key')
    except ValueError as e:
        return None, get_text('parse_failed').format(str(e))
    except Exception as e:
        return None, get_text('parse_failed').format(str(e))


def execute_custom_schedule(
    spec: StaffingSpec,
    basic_params: Dict[str, Any],
) -> tuple[Optional[str], int, Optional[float]]:
    """Step 2: Run the optimizer from a validated StaffingSpec."""
    return run_custom_schedule(spec, basic_params)


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
    # Custom tab state
    if 'custom_spec' not in st.session_state:
        st.session_state.custom_spec = None
    if 'custom_parse_error' not in st.session_state:
        st.session_state.custom_parse_error = None
    if 'custom_basic_params' not in st.session_state:
        st.session_state.custom_basic_params = {}
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([get_text('nurses_tab'), get_text('caregivers_tab'), get_text('custom_tab')])
    
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
                value=st.session_state.nb_part_time_agents,
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
    
    with tab3:
        st.header(get_text('custom_header'))

        col1, col2 = st.columns(2)

        with col1:
            st.subheader(get_text('general_params'))
            st.session_state.custom_nb_agents = st.number_input(
                get_text('nb_agents'),
                min_value=1,
                max_value=50,
                value=10,
                key="custom_agents",
                help=get_text('help_custom_agents'),
            )
            st.session_state.custom_nb_weeks = st.number_input(
                get_text('nb_weeks'),
                min_value=1,
                max_value=52,
                value=8,
                key="custom_weeks",
                help=get_text('help_weeks'),
            )
            st.session_state.custom_nb_shifts = st.number_input(
                get_text('nb_shifts'),
                min_value=1,
                max_value=5,
                value=3,
                key="custom_shifts",
                help=get_text('help_shifts'),
            )
            st.session_state.custom_nb_part_time_agents = st.number_input(
                get_text('nb_part_time_agents'),
                min_value=0,
                max_value=st.session_state.custom_nb_agents,
                value=2,
                key="custom_part_time",
                help=get_text('help_custom_part_time'),
            )

        with col2:
            st.subheader(get_text('custom_constraints'))
            st.info(get_text('custom_info'))
            user_constraints = st.text_area(
                get_text('constraints_label'),
                value="",
                height=200,
                placeholder=get_text('constraints_placeholder'),
                help=get_text('constraints_help'),
                disabled=st.session_state.custom_spec is not None,
            )

        # ── STEP 1: Parse ────────────────────────────────────────────────────
        if st.session_state.custom_spec is None:
            if st.button(get_text('parse_constraints'), type="primary"):
                if not user_constraints.strip():
                    st.error(get_text('constraints_empty'))
                else:
                    basic_params = {
                        'nb_agents': st.session_state.custom_nb_agents,
                        'nb_weeks': st.session_state.custom_nb_weeks,
                        'nb_shifts': st.session_state.custom_nb_shifts,
                        'nb_part_time_agents': st.session_state.custom_nb_part_time_agents,
                    }
                    with st.spinner(get_text('parsing_constraints')):
                        lang = st.session_state.get('language', 'en')
                        spec, error = parse_custom_constraints(user_constraints, basic_params, lang=lang)

                    if error:
                        st.session_state.custom_parse_error = error
                    else:
                        st.session_state.custom_spec = spec
                        st.session_state.custom_parse_error = None
                        st.session_state.custom_basic_params = basic_params
                        st.rerun()

            if st.session_state.custom_parse_error:
                st.error(st.session_state.custom_parse_error)

        # ── STEP 2: Confirm & Run ────────────────────────────────────────────
        else:
            spec: StaffingSpec = st.session_state.custom_spec
            lang = st.session_state.get('language', 'en')

            st.success(get_text('parse_success'))
            st.subheader(get_text('parsed_constraints_title'))
            st.text(spec.to_human_readable(lang=lang))

            if spec.notes:
                st.warning(f"{get_text('llm_notes')}\n\n{spec.notes}")

            col_edit, col_confirm = st.columns(2)

            with col_edit:
                if st.button(get_text('edit_constraints')):
                    st.session_state.custom_spec = None
                    st.session_state.custom_parse_error = None
                    st.rerun()

            with col_confirm:
                if st.button(get_text('confirm_and_run'), type="primary"):
                    with st.spinner(get_text('running_optimization')):
                        output_path, status_code, objective = execute_custom_schedule(
                            spec,
                            st.session_state.custom_basic_params,
                        )

                    if output_path and os.path.exists(output_path):
                        st.success(get_text('success_custom'))
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(get_text('status'), LpStatus[status_code])
                        with col2:
                            st.metric(get_text('objective_value'), f"{objective:.1f}")
                        with col3:
                            st.metric(get_text('output_file'), "custom_schedule.xlsx")
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label=get_text('download_custom'),
                                data=f.read(),
                                file_name="custom_schedule.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            )
                    else:
                        status_label = LpStatus.get(status_code, str(status_code))
                        st.warning(get_text('infeasible_warning').format(status_label))
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: #666;'>
        <p>{get_text('footer_text')}</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main() 