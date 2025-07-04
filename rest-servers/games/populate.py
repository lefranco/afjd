#!/usr/bin/env python3


"""
File : populate.py

Data : populate database
"""

import mylogger
import actives
import submissions
import communication_orders
import orders
import ownerships
import units
import imagined_units
import forbiddens
import reports
import capacities
import transitions
import games
import contents
import declarations
import messages
import allocations
import visits
import definitives
import incidents
import incidents2
import votes
import notes
import assignments
import tournaments
import groupings
import dropouts
import replacements
import database


def populate_transitions(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    transitions.Transition.create_table(sql_executor)


def populate_reports(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    reports.Report.create_table(sql_executor)


def populate_capacities(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    capacities.Capacity.create_table(sql_executor)


def populate_actives(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    actives.Active.create_table(sql_executor)


def populate_submissions(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    submissions.Submission.create_table(sql_executor)


def populate_orders(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    orders.Order.create_table(sql_executor)


def populate_communication_orders(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    communication_orders.CommunicationOrder.create_table(sql_executor)


def populate_ownerships(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    ownerships.Ownership.create_table(sql_executor)


def populate_units(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    units.Unit.create_table(sql_executor)


def populate_imagined_units(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    imagined_units.ImaginedUnit.create_table(sql_executor)


def populate_forbiddens(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    forbiddens.Forbidden.create_table(sql_executor)


def populate_games(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    games.Game.create_table(sql_executor)


def populate_contents(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    contents.Content.create_table(sql_executor)


def populate_declarations(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    declarations.Declaration.create_table(sql_executor)


def populate_messages(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    messages.Message.create_table(sql_executor)


def populate_allocations(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    allocations.Allocation.create_table(sql_executor)


def populate_visits(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    visits.Visit.create_table(sql_executor)


def populate_votes(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    votes.Vote.create_table(sql_executor)


def populate_notes(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    notes.Note.create_table(sql_executor)


def populate_definitives(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    definitives.Definitive.create_table(sql_executor)


def populate_incidents(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    incidents.Incident.create_table(sql_executor)


def populate_incidents2(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    incidents2.Incident2.create_table(sql_executor)


def populate_tournaments(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    tournaments.Tournament.create_table(sql_executor)


def populate_assignments(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    assignments.Assignment.create_table(sql_executor)


def populate_groupings(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    groupings.Grouping.create_table(sql_executor)


def populate_dropouts(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    dropouts.Dropout.create_table(sql_executor)


def populate_replacements(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    replacements.Replacement.create_table(sql_executor)


def populate(sql_executor: database.SqlExecutor) -> None:
    """ inserts all items in database """

    mylogger.LOGGER.warning("Populating...")

    populate_transitions(sql_executor)
    populate_reports(sql_executor)
    populate_capacities(sql_executor)
    populate_actives(sql_executor)
    populate_submissions(sql_executor)
    populate_communication_orders(sql_executor)
    populate_orders(sql_executor)
    populate_ownerships(sql_executor)
    populate_units(sql_executor)
    populate_imagined_units(sql_executor)
    populate_forbiddens(sql_executor)
    populate_games(sql_executor)
    populate_messages(sql_executor)
    populate_declarations(sql_executor)
    populate_contents(sql_executor)
    populate_allocations(sql_executor)
    populate_visits(sql_executor)
    populate_votes(sql_executor)
    populate_definitives(sql_executor)
    populate_incidents(sql_executor)
    populate_incidents2(sql_executor)
    populate_tournaments(sql_executor)
    populate_assignments(sql_executor)
    populate_groupings(sql_executor)
    populate_dropouts(sql_executor)
    populate_replacements(sql_executor)


if __name__ == '__main__':
    assert False, "Do not run this script"
