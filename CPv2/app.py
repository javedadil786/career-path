from flask import Flask, render_template, request, redirect, url_for

from database import configure_database

from player import (
    generate_starting_stats,
    calculate_overall,
    generate_potential,
)
from season import (
    play_season,
    retirement_check,
    build_career_summary,
)
from transfers import (
    generate_web_transfer_offers,
    complete_web_transfer,
)


app = Flask(__name__)

configure_database(app)

current_player = None
pending_transfer_offers = []


def build_web_player(name, nationality, position):
    pace, shooting, passing, defending = (
        generate_starting_stats(position)
    )

    overall = calculate_overall(
        position,
        pace,
        shooting,
        passing,
        defending,
    )

    potential = generate_potential(overall)

    return {
        "name": name,
        "age": 15,
        "nationality": nationality,
        "position": position,
        "club": "Youth Academy",

        "pace": pace,
        "shooting": shooting,
        "passing": passing,
        "defending": defending,

        "overall": overall,
        "potential": potential,
        "peak_overall": overall,

        "season": 1,
        "overall_history": [],

        "career_matches": 0,
        "career_goals": 0,
        "career_assists": 0,
        "career_saves": 0,
        "career_clean_sheets": 0,

        "career_rating_total": 0.0,
        "career_rating_seasons": 0,
        "career_seasons": 0,

        "league_titles": 0,
        "domestic_cups": 0,
        "champions_leagues": 0,
        "world_cups": 0,
        "euros": 0,

        "ballon_dors": 0,
        "golden_boots": 0,
        "team_of_seasons": 0,

        "season_matches": 0,
        "season_goals": 0,
        "season_assists": 0,
        "season_saves": 0,
        "season_clean_sheets": 0,
        "season_rating": 0.0,

        "injured": False,
        "injury_name": "",
        "injury_games": 0,

        "contract_years": 0,
        "weekly_wage": 0,
        "squad_role": "Academy Player",

        "clubs_history": ["Youth Academy"],
        "biggest_transfer_fee": 0,
        "last_transfer_season": -100,

        "international_caps": 0,
        "international_goals": 0,
        "international_assists": 0,
        "international_saves": 0,
        "international_clean_sheets": 0,
        "world_cup_appearances": 0,
        "euros_appearances": 0,

        "won_league_this_season": False,
        "won_cup_this_season": False,
        "won_ucl_this_season": False,
        "won_world_cup_this_season": False,
        "won_euros_this_season": False,

        "retired": False,
        "retirement_reason": "",
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route(
    "/create-player",
    methods=["GET", "POST"],
)
def create_player_page():
    global current_player
    global pending_transfer_offers

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        nationality = request.form.get(
            "nationality",
            "England",
        ).strip()
        position = request.form.get(
            "position",
            "Striker",
        ).strip()

        if not name:
            return render_template(
                "create_player.html",
                error="Please enter a player name.",
            )

        current_player = build_web_player(
            name,
            nationality,
            position,
        )
        pending_transfer_offers = []

        return redirect(
            url_for("career_page")
        )

    return render_template("create_player.html")


@app.route("/career")
def career_page():
    if current_player is None:
        return redirect(
            url_for("create_player_page")
        )

    summary = None

    if current_player.get("retired", False):
        summary = build_career_summary(
            current_player
        )

    return render_template(
        "career.html",
        player=current_player,
        transfer_offers=pending_transfer_offers,
        summary=summary,
    )


@app.route(
    "/play-season",
    methods=["POST"],
)
def play_next_season():
    global current_player
    global pending_transfer_offers

    if current_player is None:
        return redirect(
            url_for("create_player_page")
        )

    if current_player.get("retired", False):
        return redirect(
            url_for("career_page")
        )

    if pending_transfer_offers:
        return redirect(
            url_for("career_page")
        )

    play_season(
        current_player,
        web_mode=True,
    )

    if retirement_check(current_player):
        current_player["retired"] = True
        current_player["retirement_reason"] = (
            "Automatic retirement"
        )
        pending_transfer_offers = []

        return redirect(
            url_for("career_page")
        )

    completed_season = (
        current_player.get("season", 1) - 1
    )

    pending_transfer_offers = (
        generate_web_transfer_offers(
            current_player,
            completed_season,
        )
    )

    return redirect(
        url_for("career_page")
    )


@app.route(
    "/accept-transfer/<int:offer_index>",
    methods=["POST"],
)
def accept_transfer(offer_index):
    global current_player
    global pending_transfer_offers

    if current_player is None:
        return redirect(
            url_for("create_player_page")
        )

    if current_player.get("retired", False):
        return redirect(
            url_for("career_page")
        )

    if not (
        0 <= offer_index
        < len(pending_transfer_offers)
    ):
        return redirect(
            url_for("career_page")
        )

    completed_season = (
        current_player.get("season", 1) - 1
    )

    selected_offer = pending_transfer_offers[
        offer_index
    ]

    complete_web_transfer(
        current_player,
        selected_offer,
        completed_season,
    )

    pending_transfer_offers = []

    return redirect(
        url_for("career_page")
    )


@app.route(
    "/reject-transfers",
    methods=["POST"],
)
def reject_transfers():
    global pending_transfer_offers

    pending_transfer_offers = []

    return redirect(
        url_for("career_page")
    )


@app.route(
    "/retire",
    methods=["POST"],
)
def retire_player():
    global current_player
    global pending_transfer_offers

    if current_player is None:
        return redirect(
            url_for("create_player_page")
        )

    current_player["retired"] = True
    current_player["retirement_reason"] = (
        "Player chose to retire"
    )
    pending_transfer_offers = []

    return redirect(
        url_for("career_page")
    )


@app.route("/statistics")
def statistics_page():
    if current_player is None:
        return redirect(
            url_for("create_player_page")
        )

    return render_template(
        "statistics.html",
        player=current_player,
    )


if __name__ == "__main__":
    app.run(debug=True)