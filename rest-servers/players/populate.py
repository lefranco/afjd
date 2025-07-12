#!/usr/bin/env python3


"""
File : populate.py

Data : populate database
"""

import mylogger
import newss
import moderators
import blacklisteds
import creators
import players
import ratings
import ratings2
import ratings3
import teasers
import events
import site_image
import registrations
import timezones
import addresses
import submissions
import emails
import database
import contents
import messages


def populate_newss(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    newss.News.create_table(sql_executor)


def populate_players(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    players.Player.create_table(sql_executor)


def populate_moderators(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    moderators.Moderator.create_table(sql_executor)


def populate_blacklisteds(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    blacklisteds.Blacklisted.create_table(sql_executor)


def populate_creators(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    creators.Creator.create_table(sql_executor)


def populate_ratings(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    ratings.Rating.create_table(sql_executor)


def populate_ratings2(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    ratings2.Rating2.create_table(sql_executor)


def populate_ratings3(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    ratings3.Rating3.create_table(sql_executor)


def populate_teasers(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    teasers.Teaser.create_table(sql_executor)


def populate_events(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    events.Event.create_table(sql_executor)


def populate_site_image(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    site_image.SiteImage.create_table(sql_executor)


def populate_registrations(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    registrations.Registration.create_table(sql_executor)


def populate_timezones(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    timezones.Timezone.create_table(sql_executor)


def populate_addresses(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    addresses.Address.create_table(sql_executor)


def populate_submissions(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    submissions.Submission.create_table(sql_executor)


def populate_emails(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    emails.Email.create_table(sql_executor)


def populate_contents(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    contents.Content.create_table(sql_executor)


def populate_messages(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """
    messages.Message.create_table(sql_executor)


def populate(sql_executor: database.SqlExecutor) -> None:
    """ inserts all items in database """

    mylogger.LOGGER.warning("Populating...")

    populate_newss(sql_executor)
    populate_players(sql_executor)
    populate_moderators(sql_executor)
    populate_blacklisteds(sql_executor)
    populate_creators(sql_executor)
    populate_ratings(sql_executor)
    populate_ratings2(sql_executor)
    populate_ratings3(sql_executor)
    populate_teasers(sql_executor)
    populate_events(sql_executor)
    populate_site_image(sql_executor)
    populate_registrations(sql_executor)
    populate_timezones(sql_executor)
    populate_addresses(sql_executor)
    populate_submissions(sql_executor)
    populate_emails(sql_executor)
    populate_contents(sql_executor)
    populate_messages(sql_executor)


if __name__ == '__main__':
    assert False, "Do not run this script"
