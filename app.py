from flask import Flask, render_template, request, flash
import pandas as pd
import numpy as np
import matplotlib
import seaborn as sns

matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)


@app.route('/')
def home():  # put application's code here
    data = pd.read_excel(r'BattedBallData.xlsx')
    data = data.drop(columns=['HIT_SPIN_RATE'])
    undefined_result = data['PLAY_OUTCOME'] == 'Undefined'
    data = data[~undefined_result]
    hitters = list(data['BATTER'].unique())
    pitchers = list(data['PITCHER'].unique())
    hitters.sort()
    pitchers.sort()
    ev_by_outcome = calculate_outcome_averages(data)
    casted_outcomes = data['PLAY_OUTCOME'].apply(map_outcome)
    numeric_data = data.select_dtypes(include=['number'])
    numeric_data['PLAY_OUTCOME'] = casted_outcomes
    correlation_matrix = numeric_data.corr()
    plt.figure(figsize=(12, 12))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
    plt.savefig('static/correlation_matrix.png')
    plt.close()
    rank_by_ev = calculate_batter_rankings(data)
    rank_by_ev_allowed = calculate_pitcher_rankings(data)
    return render_template('home.html', data=data, hitters=hitters, pitchers=pitchers,
                           evs=ev_by_outcome, correlation_matrix=correlation_matrix, rank_by_ev=rank_by_ev,
                           rank_by_ev_allowed=rank_by_ev_allowed)


def map_outcome(outcome):
    if outcome in ['Single', 'Double', 'Triple', 'HomeRun']:
        return 1
    else:
        return 0


@app.route('/mouse')
def mouse_program():
    return render_template('MousePos1.html')


@app.route('/outcomeaverages')
def calculate_outcome_averages(data):
    outcomes = ['Single', 'Double', 'Triple', 'HomeRun', 'Out', 'Sacrifice', 'FieldersChoice', 'Error']
    average_ev = []
    total_ev = [0, 0, 0, 0, 0, 0, 0, 0]
    for i in range(len(outcomes)):
        total_ev[i] = data['PLAY_OUTCOME'] == outcomes[i]
        average_ev.append(data.loc[total_ev[i], 'EXIT_SPEED'].mean())
    outcomes[6] = 'FC'
    outcomes[5] = 'Sac'
    plt.bar(outcomes, average_ev)
    plt.title('Average Exit Velo of all balls in play, sorted by outcome')
    plt.savefig('static/ev_by_outcome.png')
    plt.close()
    return average_ev


@app.route('/batter_rankings')
def calculate_batter_rankings(data):
    average_exit_speeds = data.groupby(['BATTER'])['EXIT_SPEED'].mean()
    ranked_hitters = average_exit_speeds.sort_values(ascending=False)
    ranked_hitters = ranked_hitters.reset_index(drop=False, inplace=False)
    return ranked_hitters


@app.route('/pitcher_rankings')
def calculate_pitcher_rankings(data):
    average_exit_speeds = data.groupby(['PITCHER'])['EXIT_SPEED'].mean()
    ranked_pitchers = average_exit_speeds.sort_values(ascending=True)
    ranked_pitchers = ranked_pitchers.reset_index(drop=False, inplace=False)
    average_hang_time = data.groupby(['PITCHER'])['HANG_TIME'].mean()
    ranked_pitchers_hang_time = average_hang_time.sort_values(ascending=True)
    ranked_pitchers_hang_time = ranked_pitchers_hang_time.reset_index(drop=False, inplace=False)
    return ranked_pitchers, ranked_pitchers_hang_time


@app.route('/show_hitter', methods=['POST'])
def show_hitter():
    hitter = request.form.get('hitter_name')
    if not hitter:
        return render_template('home.html')
    data = pd.read_excel(r'BattedBallData.xlsx')
    data = data.drop(columns=['HIT_SPIN_RATE'])
    undefined_result = data['PLAY_OUTCOME'] == 'Undefined'
    data = data[~undefined_result]
    relevant_data = data[data['BATTER'] == hitter]
    hitter_id = relevant_data['BATTER_ID'].iloc[0]
    generate_spraychart(relevant_data, hitter_id)

    average_ev = relevant_data['EXIT_SPEED'].mean().round(2)
    rank_by_ev = calculate_batter_rankings(data)
    ranking = (rank_by_ev[rank_by_ev['BATTER'] == hitter].index + 1).item()
    max_ev_idx = relevant_data['EXIT_SPEED'].idxmax()
    max_ev_num = relevant_data.loc[max_ev_idx, 'EXIT_SPEED'].round(2)
    max_ev_link = relevant_data.loc[max_ev_idx, 'VIDEO_LINK']
    return render_template('hitter_info.html', hitter=hitter, chartpath=f'static//scatterplot{hitter_id}.png', max_EV_num=max_ev_num, max_EV_link=max_ev_link, average_ev=average_ev, ranking=ranking)


@app.route('/generate_spraychart')
def generate_spraychart(relevant_data, hitter_id):
    spraychart = pd.DataFrame()
    spraychart['x'] = relevant_data['HIT_DISTANCE'] * np.sin(np.radians(relevant_data['EXIT_DIRECTION']))
    spraychart['y'] = relevant_data['HIT_DISTANCE'] * np.cos(np.radians(relevant_data['EXIT_DIRECTION']))
    plt.scatter(spraychart['x'], spraychart['y'])
    background = plt.imread('static/blankchart.png')
    plt.xticks([])
    plt.yticks([])
    plt.imshow(background, extent=(-231 / 2, 231 / 2, -125, 450), aspect='auto')
    plt.savefig(f'static//scatterplot{hitter_id}.png')
    plt.close()


@app.route('/show_pitcher', methods=['POST'])
def show_pitcher():
    pitcher = request.form.get('pitcher_name')
    if not pitcher:
        return render_template('home.html')
    data = pd.read_excel(r'C:\Users\krbig\OneDrive\Desktop\ATLBraves_assessment_Biggers\BattedBallData.xlsx')
    data = data.drop(columns=['HIT_SPIN_RATE'])
    undefined_result = data['PLAY_OUTCOME'] == 'Undefined'
    data = data[~undefined_result]
    relevant_data = data[data['PITCHER'] == pitcher]
    average_ev_against = relevant_data['EXIT_SPEED'].mean().round(2)
    average_hang_time = relevant_data['HANG_TIME'].mean().round(2)
    rank_by_ev, rank_by_hang_time = calculate_pitcher_rankings(data)
    ranking = (rank_by_ev[rank_by_ev['PITCHER'] == pitcher].index + 1).item()
    hang_time_ranking = (rank_by_hang_time[rank_by_hang_time['PITCHER'] == pitcher].index + 1).item()
    return render_template('pitcher_info.html', pitcher=pitcher, average_ev_against=average_ev_against,
                           ranking=ranking, average_hang_time=average_hang_time,
                           rank_by_hang_time=hang_time_ranking)


if __name__ == '__main__':
    app.run()
