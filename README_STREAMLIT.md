# FairnessNSP Streamlit Web Interface

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- uv package manager
- All dependencies installed (see main README)

### Running the Web Interface

1. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

2. **Start the Streamlit app:**
   ```bash
   streamlit run streamlit_app.py
   ```

3. **Open your browser:**
   Navigate to `http://localhost:8501` (or the port shown in the terminal)

## 🏥 Features

### Nurse Scheduling Tab
- **Configurable Parameters:**
  - Number of nurses (total and part-time)
  - Number of weeks to schedule
  - Number of shift types
  - Staffing requirements for weekdays and weekends

- **Real-time Optimization:**
  - Click "Generate Nurse Schedule" to run the ILP solver
  - View optimization status and objective value
  - Download the generated Excel schedule

### Caregiver Scheduling Tab
- **Simplified Interface:**
  - Basic parameters (number of agents, weeks, shifts)
  - Hardcoded constraints based on hospital requirements
  - Same optimization and download capabilities

## 📊 Output

The application generates Excel files with:
- Color-coded schedule grids
- Agent names with workload percentages
- Week-by-week layout with weekends split
- Summary statistics and constraint validation

## 🔧 Configuration

### Streamlit Settings
- **Theme:** Medical-themed with red accent color
- **Layout:** Wide layout for better parameter visibility
- **Port:** Default 8501 (configurable)

### Default Values
- **Nurses:** 11 total, 3 part-time, 10 weeks
- **Caregivers:** 9 total, 1 part-time, 10 weeks
- **Shifts:** 3 types (morning, evening, day)

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   streamlit run streamlit_app.py --server.port 8502
   ```

2. **Dependencies missing:**
   ```bash
   uv sync
   ```

3. **Virtual environment not activated:**
   ```bash
   source .venv/bin/activate
   ```

### Error Messages
- **"Error during scheduling":** Check parameter values and constraints
- **"Failed to generate schedule":** Verify staffing requirements are feasible
- **"Module not found":** Ensure all dependencies are installed

## 🎯 Usage Tips

1. **Start with default values** and adjust gradually
2. **Check staffing requirements** - ensure they're realistic for your team size
3. **Monitor the objective value** - higher values indicate better fairness
4. **Download and review** the Excel output for schedule quality

## 🔄 Integration

The Streamlit interface uses the same refactored backend as the command-line tools:
- `scheduler_core.py` - Base optimization framework
- `nurse_scheduler.py` - Nurse-specific constraints
- `caregiver_scheduler.py` - Caregiver-specific constraints
- `excel_export.py` - Excel output generation

## 📈 Future Enhancements

- Schedule visualization in the browser
- Constraint validation feedback
- Historical schedule comparison
- Multi-hospital support
- LLM-powered constraint generation 