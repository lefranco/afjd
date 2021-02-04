#!/usr/bin/env python3

"""
an ihm based on tkinter
this module handles the canvas, the left hand sid pârt of the screen with the map and enverythong that moves on it
"""

import typing
import enum
import abc

import tkinter

import font
import data
import forbiddens
import ownerships
import units
import orders

# radius to detect a mous click is inside zone
CLICKABLE_ZONE_RADIUS = 20

IMPOSED_MAP_WIDTH = 630
IMPOSED_MAP_HEIGHT = 535


class ClickableZone:
    """ A clickable zone """

    def __init__(self, x_pos: int, y_pos: int, radius: int, identifier: int) -> None:

        self._x_pos = x_pos
        self._y_pos = y_pos
        self._radius = radius
        self._identifier = identifier

    def is_inside(self, x_mouse: int, y_mouse: int) -> bool:
        """ is inside the clickable zone """
        return (x_mouse - self._x_pos) ** 2 + (y_mouse - self._y_pos) ** 2 <= CLICKABLE_ZONE_RADIUS ** 2

    @property
    def identifier(self) -> int:
        """ property """
        return self._identifier


@enum.unique
class ButtonEnum(enum.Enum):
    """ Button that was clicked """

    LEFT_BUTTTON = enum.auto()
    MIDDLE_BUTTTON = enum.auto()
    RIGHT_BUTTTON = enum.auto()


@enum.unique
class InputAutomatonStateEnum(enum.Enum):
    """ Automaton state for order entry or unit position / center ownership edition """

    STATE_INIT = enum.auto()
    STATE_A = enum.auto()
    STATE_B = enum.auto()
    STATE_C = enum.auto()
    STATE_D = enum.auto()
    STATE_E = enum.auto()
    STATE_F = enum.auto()
    STATE_G = enum.auto()
    STATE_H = enum.auto()
    STATE_I = enum.auto()
    STATE_J = enum.auto()
    STATE_K = enum.auto()
    STATE_END = enum.auto()


class InputAutomaton(abc.ABC):
    """ An generic automaton to enter orders / unit position / center ownerships """

    @abc.abstractmethod
    def change_state(self, button_clicked: ButtonEnum, zone_designed: typing.Optional[int]) -> None:
        """ should handle click  """


class MoveOrderAutomaton(InputAutomaton):
    """ An automaton to enter move orders """

    def __init__(self, canvas: 'MyCanvas') -> None:

        self._canvas = canvas
        self._state = InputAutomatonStateEnum.STATE_INIT
        self._order = orders.Order(self._canvas)

    def change_state(self, button_clicked: ButtonEnum, zone_designed: typing.Optional[int]) -> None:
        """ make the automaton moves """

        if button_clicked is ButtonEnum.LEFT_BUTTTON:
            # Purpose of this button is to select the active unit, the passive unit and the destination

            assert zone_designed is not None
            zone_name = data.find_zone_name(zone_designed)

            if self._state is InputAutomatonStateEnum.STATE_A:

                assert self._order.active_unit is not None
                direct = self._order.active_unit.may_move_there_direct(zone_designed)
                convoy = self._order.active_unit.may_move_there_by_convoy(zone_designed)
                if not (direct or convoy):
                    self._canvas.application.label_dynamic_information.config(text=f"Ce déplacement n'est pas possible, sélectionnez une autre destination pour {self._order.active_unit}")
                    return

                convoy_message = "Ce déplacement sera forcément par convoi\n" if not direct else ""

                self._order.destination_zone = zone_designed
                self._canvas.application.label_dynamic_information.config(text=f"{convoy_message}Cliquez droit pour finaliser le déplacement de {self._order.active_unit} vers {zone_name}\n(ou cliquez droit pour abandonner).")
                self._state = InputAutomatonStateEnum.STATE_F

            elif self._state is InputAutomatonStateEnum.STATE_B:

                passive_unit = self._canvas.bag_units.find_unit(zone_designed)
                if passive_unit is None:
                    self._canvas.application.label_dynamic_information.config(text=f"Il n'y a pas d'unité à cet endroit ({zone_name})\nCliquez gauche sur une unité à supporter offensivement.")
                    return

                self._order.passive_unit = passive_unit
                self._canvas.application.label_dynamic_information.config(text=f"L'unité soutenue offensivement est {self._order.passive_unit}.\nSélectionnez maintenant la destination de l'attaque soutenue\n(ou cliquez droit pour abandonner).")
                self._state = InputAutomatonStateEnum.STATE_G

            elif self._state is InputAutomatonStateEnum.STATE_C:

                passive_unit = self._canvas.bag_units.find_unit(zone_designed)
                if passive_unit is None:
                    self._canvas.application.label_dynamic_information.config(text=f"Il n'y a pas d'unité à cet endroit ({zone_name})\nCliquez gauche sur une unité à supporter défensivement.")
                    return

                assert self._order.active_unit is not None
                if not self._order.active_unit.may_support_there(zone_designed):
                    self._canvas.application.label_dynamic_information.config(text="Soutenir défensivement cette unité n'est pas possible, sélectionnez une autre destination")
                    return

                self._order.passive_unit = passive_unit
                self._canvas.application.label_dynamic_information.config(text=f"Cliquez droit pour finaliser le soutien défensif de {zone_name}\n(ou cliquez droit pour abandonner)")
                self._state = InputAutomatonStateEnum.STATE_I

            elif self._state is InputAutomatonStateEnum.STATE_E:

                passive_unit = self._canvas.bag_units.find_unit(zone_designed)
                if passive_unit is None:
                    self._canvas.application.label_dynamic_information.config(text=f"Il n'y a pas d'unité à cet endroit ({zone_name})\nCliquez gauche sur une autre unité à convoyer.")
                    return

                if not passive_unit.may_be_convoyed():
                    self._canvas.application.label_dynamic_information.config(text=f"Cette unité {passive_unit} ne peut pas être convoyée\nCliquez gauche sur autre une unité à convoyer.")
                    return

                self._order.passive_unit = passive_unit
                self._canvas.application.label_dynamic_information.config(text=f"L'unité convoyée est {self._order.passive_unit}.\nSélectionnez maintenant la destination du convoi.")
                self._state = InputAutomatonStateEnum.STATE_J

            # --- phase 2
            elif self._state is InputAutomatonStateEnum.STATE_G:

                assert self._order.passive_unit is not None
                direct = self._order.passive_unit.may_move_there_direct(zone_designed)
                convoy = self._order.passive_unit.may_move_there_by_convoy(zone_designed)
                if not (direct or convoy):
                    self._canvas.application.label_dynamic_information.config(text="Ce déplacement soutenu n'est pas possible, sélectionnez une autre destination\n(ou cliquez droit pour abandonner)")
                    return

                convoy_message = "Ce déplacement soutenu sera forcément par convoi\n" if not direct else ""

                assert self._order.active_unit is not None
                if not self._order.active_unit.may_support_there(zone_designed):
                    self._canvas.application.label_dynamic_information.config(text="Soutenir ce déplacement n'est pas possible, sélectionnez une autre destination\n(ou cliquez droit pour abandonner)")
                    return

                self._order.destination_zone = zone_designed
                self._canvas.application.label_dynamic_information.config(text=f"{convoy_message}Cliquez droit pour finaliser le support offensif vers {zone_name}\n(ou cliquez droit pour abandonner)")
                self._state = InputAutomatonStateEnum.STATE_H

            elif self._state is InputAutomatonStateEnum.STATE_J:

                assert self._order.passive_unit is not None
                direct = self._order.passive_unit.may_move_there_direct(zone_designed)
                convoy = self._order.passive_unit.may_move_there_by_convoy(zone_designed)
                if not (direct or convoy):
                    self._canvas.application.label_dynamic_information.config(text="Ce déplacement convoyé n'est pas possible, sélectionnez une autre destination\n(ou cliquez droit pour abandonner)")
                    return

                self._order.destination_zone = zone_designed
                self._canvas.application.label_dynamic_information.config(text=f"Cliquez droit pour finaliser le convoi vers {zone_name}\n(ou cliquez droit pour abandonner)")
                self._state = InputAutomatonStateEnum.STATE_K

            # --- start or reset
            else:

                reset_message = "Bon, on recommence!\n" if self._state is not InputAutomatonStateEnum.STATE_INIT else ""

                unit = self._canvas.bag_units.find_unit(zone_designed)
                if unit is None:
                    self._canvas.application.label_dynamic_information.config(text=f"Il n'y a pas d'unité à cet endroit ({zone_name})\nCliquez gauche sur une unité à ordonner.")
                    return

                self._order.active_unit = unit

                self._canvas.application.label_dynamic_information.config(text=f"{reset_message}L'unité sélectionnée est {zone_name}. Ordre d'attaque.\nCliquez milieu pour changer son ordre ou désignez maintenant la destination de l'attaque.")
                self._order.order_type = orders.OrderEnum.ATTACK_ORDER
                self._state = InputAutomatonStateEnum.STATE_A

        elif button_clicked is ButtonEnum.MIDDLE_BUTTTON:
            # Purpose of this button is to change the order type

            if self._order.active_unit is None:
                self._canvas.application.label_dynamic_information.config(text="Sélectionnez d'abord l'unité à ordonner sur la carte")
                return

            if self._state is InputAutomatonStateEnum.STATE_A:
                order_type_name = data.ORDERS_DATA['2']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ordre : {order_type_name} pour {self._order.active_unit}.\nCliquez milieu pour changer son ordre ou désignez maintenant l'unité soutenue.")
                self._order.order_type = orders.OrderEnum.OFFENSIVE_SUPPORT_ORDER
                self._state = InputAutomatonStateEnum.STATE_B

            elif self._state is InputAutomatonStateEnum.STATE_B:
                order_type_name = data.ORDERS_DATA['3']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ordre : {order_type_name}f pour {self._order.active_unit}.\nCliquez milieu pour changer son ordre ou désignez maintenant l'unité soutenue.")
                self._order.order_type = orders.OrderEnum.DEFENSIVE_SUPPORT_ORDER
                self._state = InputAutomatonStateEnum.STATE_C

            elif self._state is InputAutomatonStateEnum.STATE_C:
                order_type_name = data.ORDERS_DATA['4']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ordre : {order_type_name} pour : {self._order.active_unit}.\nCliquez milieu pour changer son ordre.\nCliquez droit pour finaliser l'action de rester en place (ou cliquez droit pour abandonner)")
                self._order.order_type = orders.OrderEnum.HOLD_ORDER
                self._state = InputAutomatonStateEnum.STATE_D

            elif self._state is InputAutomatonStateEnum.STATE_D:

                if not self._order.active_unit.may_convoy():
                    self._canvas.application.label_dynamic_information.config(text="Cette unité à cet endroit ne peut pas convoyer")
                    self._state = InputAutomatonStateEnum.STATE_A
                    return

                order_type_name = data.ORDERS_DATA['5']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ordre : {order_type_name} pour {self._order.active_unit}. \nCliquez milieu pour changer son ordre ou désignez maintenant l'unité convoyée.")
                self._order.order_type = orders.OrderEnum.CONVOY_ORDER
                self._state = InputAutomatonStateEnum.STATE_E

            elif self._state is InputAutomatonStateEnum.STATE_E:
                order_type_name = data.ORDERS_DATA['1']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ordre : {order_type_name} pour {self._order.active_unit}.\nCliquez milieu pour changer son ordre ou désignez maintenant la destination de l'attaque.")
                self._order.order_type = orders.OrderEnum.ATTACK_ORDER
                self._state = InputAutomatonStateEnum.STATE_A

            else:
                self._canvas.application.label_dynamic_information.config(text="Abandon.")
                self._state = InputAutomatonStateEnum.STATE_INIT

        elif button_clicked is ButtonEnum.RIGHT_BUTTTON:
            # Purpose of this button is to validate the order

            if self._order.active_unit is None:
                self._canvas.application.label_dynamic_information.config(text="Sélectionnez d'abord l'unité à ordonner sur la carte")
                return

            if self._state is InputAutomatonStateEnum.STATE_F:
                self._canvas.bag_orders.add_update_order(self._order)
                self._canvas.refresh()
                order_type_name = data.ORDERS_DATA['1']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ok pour {order_type_name}.")
                self._state = InputAutomatonStateEnum.STATE_INIT
                self._order = orders.Order(self._canvas)

            elif self._state is InputAutomatonStateEnum.STATE_H:
                self._canvas.bag_orders.add_update_order(self._order)
                self._canvas.refresh()
                order_type_name = data.ORDERS_DATA['2']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ok pour {order_type_name}.")
                self._state = InputAutomatonStateEnum.STATE_INIT
                self._order = orders.Order(self._canvas)

            elif self._state is InputAutomatonStateEnum.STATE_I:
                self._canvas.bag_orders.add_update_order(self._order)
                self._canvas.refresh()
                order_type_name = data.ORDERS_DATA['3']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ok pour {order_type_name}.")
                self._state = InputAutomatonStateEnum.STATE_INIT
                self._order = orders.Order(self._canvas)

            elif self._state is InputAutomatonStateEnum.STATE_D:
                self._canvas.bag_orders.add_update_order(self._order)
                self._canvas.refresh()
                order_type_name = data.ORDERS_DATA['4']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ok pour {order_type_name}.")
                self._state = InputAutomatonStateEnum.STATE_INIT
                self._order = orders.Order(self._canvas)

            elif self._state is InputAutomatonStateEnum.STATE_K:
                self._canvas.bag_orders.add_update_order(self._order)
                self._canvas.refresh()
                order_type_name = data.ORDERS_DATA['5']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ok pour {order_type_name}.")
                self._state = InputAutomatonStateEnum.STATE_INIT
                self._order = orders.Order(self._canvas)

            else:
                self._canvas.application.label_dynamic_information.config(text="Abandon.")
                self._state = InputAutomatonStateEnum.STATE_INIT


class RetreatOrderAutomaton(InputAutomaton):
    """ An automaton to enter retreat orders """

    def __init__(self, canvas: 'MyCanvas') -> None:

        self._canvas = canvas
        self._state = InputAutomatonStateEnum.STATE_INIT
        self._order = orders.Order(self._canvas)

    def change_state(self, button_clicked: ButtonEnum, zone_designed: typing.Optional[int]) -> None:
        """ make the automaton moves """

        assert self._canvas.application is not None

        if button_clicked is ButtonEnum.LEFT_BUTTTON:
            # Purpose of this button is to select the active unit, the passive unit and the destination

            assert zone_designed is not None
            zone_name = data.find_zone_name(zone_designed)

            # --- phase 1
            if self._state is InputAutomatonStateEnum.STATE_A:

                assert self._order.active_unit is not None
                direct = self._order.active_unit.may_move_there_direct(zone_designed)
                if not direct:
                    self._canvas.application.label_dynamic_information.config(text="Le déplacement de la retraite n'est pas possible, sélectionnez une autre destination")
                    return

                self._order.destination_zone = zone_designed
                self._canvas.application.label_dynamic_information.config(text=f"Cliquez droit pour finaliser la retraite vers {zone_name} (ou cliquez droit pour abandonner)")
                self._state = InputAutomatonStateEnum.STATE_B

            else:

                reset_message = "Bon, on recommence!\n" if self._state is not InputAutomatonStateEnum.STATE_INIT else ""

                unit = self._canvas.bag_units.find_dislodged_unit(zone_designed)
                if unit is None:
                    self._canvas.application.label_dynamic_information.config(text=f"Il n'y a pas d'unité délogée à cet endroit ({zone_name})\nCliquez gauche sur une unité à ordonner.")
                    return

                self._order.active_unit = unit

                self._canvas.application.label_dynamic_information.config(text=f"{reset_message}L'unité sélectionnée est {zone_name}. Ordre de retraite.\nCliquez milieu pour changer son ordre ou désignez maintenant la destination de la retraite.")
                self._order.order_type = orders.OrderEnum.RETREAT_ORDER
                self._state = InputAutomatonStateEnum.STATE_A

        elif button_clicked is ButtonEnum.MIDDLE_BUTTTON:
            # Purpose of this button is to change the order type

            if self._order.active_unit is None:
                self._canvas.application.label_dynamic_information.config(text="Sélectionnez d'abord l'unité à ordonner sur la carte")
                return

            if self._state is InputAutomatonStateEnum.STATE_A:
                order_type_name = data.ORDERS_DATA['7']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ordre : {order_type_name} pour {self._order.active_unit}.\nCliquez droit pour confirmer.")
                self._order.order_type = orders.OrderEnum.DISBAND_ORDER
                self._state = InputAutomatonStateEnum.STATE_C

            elif self._state is InputAutomatonStateEnum.STATE_C:
                order_type_name = data.ORDERS_DATA['6']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ordre : {order_type_name} pour {self._order.active_unit}.\nCliquez milieu pour changer son ordre ou désignez maintenant la destination de la retraite.")
                self._order.order_type = orders.OrderEnum.RETREAT_ORDER
                self._state = InputAutomatonStateEnum.STATE_A

            else:
                self._canvas.application.label_dynamic_information.config(text="Abandon.")
                self._state = InputAutomatonStateEnum.STATE_INIT

        elif button_clicked is ButtonEnum.RIGHT_BUTTTON:
            # Purpose of this button is to validate the order

            if self._order.active_unit is None:
                self._canvas.application.label_dynamic_information.config(text="Sélectionnez d'abord l'unité à ordonner sur la carte")
                return

            if self._state is InputAutomatonStateEnum.STATE_B:
                self._canvas.bag_orders.add_update_order(self._order)
                self._canvas.refresh()
                order_type_name = data.ORDERS_DATA['6']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ok pour {order_type_name}.")
                self._state = InputAutomatonStateEnum.STATE_INIT
                self._order = orders.Order(self._canvas)

            elif self._state is InputAutomatonStateEnum.STATE_C:
                self._canvas.bag_orders.add_update_order(self._order)
                self._canvas.refresh()
                order_type_name = data.ORDERS_DATA['7']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ok pour {order_type_name}.")
                self._state = InputAutomatonStateEnum.STATE_INIT
                self._order = orders.Order(self._canvas)

            else:
                self._canvas.application.label_dynamic_information.config(text="Abandon.")
                self._state = InputAutomatonStateEnum.STATE_INIT


class AdjustmentOrderAutomaton(InputAutomaton):
    """ An automaton to enter adjustment orders """

    def __init__(self, canvas: 'MyCanvas') -> None:

        self._canvas = canvas
        self._state = InputAutomatonStateEnum.STATE_INIT
        self._order = orders.Order(self._canvas)

    def change_state(self, button_clicked: ButtonEnum, zone_designed: typing.Optional[int]) -> None:
        """ make the automaton moves """

        assert self._canvas.application is not None

        if button_clicked is ButtonEnum.LEFT_BUTTTON:
            # Purpose of this button is to select the active unit, the passive unit and the destination

            assert zone_designed is not None
            zone_name = data.find_zone_name(zone_designed)

            unit = self._canvas.bag_units.find_unit(zone_designed)
            if unit is not None:
                self._state = InputAutomatonStateEnum.STATE_A
                order_type_name = data.ORDERS_DATA['9']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ordre : {order_type_name} pour {zone_name}.\nCliquez droit pour confirmer.")
                self._order.order_type = orders.OrderEnum.REMOVE_ORDER
                self._order.active_unit = unit
            else:

                role = data.may_build_there(zone_designed)
                if role is None:
                    self._canvas.application.label_dynamic_information.config(text="Il n'est pas possible de construire à cet endroit, sélectionnez un autre emplacement")
                    return

                role_name = data.ROLE_DATA[str(role)]['name']
                unit_type = data.UNIT_DATA['1']['name']  # starts with army
                order_type_name = data.ORDERS_DATA['8']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ordre : {order_type_name} pour {unit_type} en {zone_name} pour le role {role_name}.\nCliquez droit pour confirmer ou cliquez milieu pour changer")
                self._state = InputAutomatonStateEnum.STATE_B
                self._order.order_type = orders.OrderEnum.BUILD_ORDER

                # Make a fake unit for the order
                assert role is not None
                assert zone_designed is not None
                self._order.active_unit = units.Unit(self._canvas, data.TypeUnitEnum.ARMY_TYPE, role, zone_designed, None)

        elif button_clicked is ButtonEnum.MIDDLE_BUTTTON:
            # Purpose of this button is to change the order type

            if self._state is InputAutomatonStateEnum.STATE_B:
                unit_type = data.UNIT_DATA['2']['name']
                self._canvas.application.label_dynamic_information.config(text=f"On change en : {unit_type}.\nCliquez droit pour confirmer ou cliquez milieu pour changer")
                self._state = InputAutomatonStateEnum.STATE_C

            elif self._state is InputAutomatonStateEnum.STATE_C:
                unit_type = data.UNIT_DATA['1']['name']
                self._canvas.application.label_dynamic_information.config(text=f"On change en : {unit_type}.\nCliquez droit pour confirmer ou cliquez milieu pour changer")
                self._state = InputAutomatonStateEnum.STATE_B

            else:
                self._canvas.application.label_dynamic_information.config(text="Abandon.")
                self._state = InputAutomatonStateEnum.STATE_INIT

        elif button_clicked is ButtonEnum.RIGHT_BUTTTON:
            # Purpose of this button is to validate the order

            if self._state is InputAutomatonStateEnum.STATE_A:
                self._canvas.bag_orders.add_update_order(self._order)
                self._canvas.refresh()
                order_type_name = data.ORDERS_DATA['9']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ok pour {order_type_name}.")
                self._state = InputAutomatonStateEnum.STATE_INIT
                self._order = orders.Order(self._canvas)

            elif self._state is InputAutomatonStateEnum.STATE_B:
                assert self._order.active_unit is not None
                self._order.active_unit.type_unit = data.TypeUnitEnum.ARMY_TYPE
                self._canvas.bag_orders.add_update_order(self._order)
                self._canvas.refresh()
                unit_type = data.UNIT_DATA['1']['name']
                order_type_name = data.ORDERS_DATA['8']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ok pour {order_type_name} pour {unit_type}.")
                self._state = InputAutomatonStateEnum.STATE_INIT
                self._order = orders.Order(self._canvas)

            elif self._state is InputAutomatonStateEnum.STATE_C:
                assert self._order.active_unit is not None
                self._order.active_unit.type_unit = data.TypeUnitEnum.FLEET_TYPE
                self._canvas.bag_orders.add_update_order(self._order)
                self._canvas.refresh()
                unit_type = data.UNIT_DATA['2']['name']
                self._canvas.application.label_dynamic_information.config(text=f"Ok pour une construction de : {unit_type}.")
                self._state = InputAutomatonStateEnum.STATE_INIT
                self._order = orders.Order(self._canvas)

            else:
                self._canvas.application.label_dynamic_information.config(text="Abandon.")
                self._state = InputAutomatonStateEnum.STATE_INIT


class PositionEditionAutomaton(InputAutomaton):
    """ An automaton to edit unit positions """

    def __init__(self, canvas: 'MyCanvas') -> None:

        self._canvas = canvas
        self._state = InputAutomatonStateEnum.STATE_INIT
        self._zone_designed: typing.Optional[int] = None

    def change_state(self, button_clicked: ButtonEnum, zone_designed: typing.Optional[int]) -> None:
        """ Make the automaton moves (actually this automatons stays in init state) """

        assert self._canvas.application is not None

        if button_clicked is ButtonEnum.LEFT_BUTTTON:
            # Purpose of this button is put unit or not

            assert zone_designed is not None
            unit = self._canvas.bag_units.find_unit(zone_designed)

            if zone_designed == self._zone_designed:
                if unit is not None:
                    self._canvas.application.label_dynamic_information.config(text=f"Suppression de {unit}.")
                    self._canvas.bag_units.remove_unit(unit)

                    # redraw canvas (not very optmized !)
                    self._canvas.refresh()

                    self._zone_designed = None
                    return

            self._zone_designed = zone_designed

            if unit is not None:
                self._canvas.application.label_dynamic_information.config(text=f"Sélection de {unit}. Cliquez gauche pour supprimer cette unité.\nCliquez milieu pour changer son type.\nCliquez droit pour changer son rôle")
                return

            for unit_type in data.TypeUnitEnum:
                unit = units.Unit(self._canvas, unit_type, 1, zone_designed, None)
                if unit.may_appear():
                    break
            else:
                assert False, "Cannot create unit"
                return

            # check not occupied
            if self._canvas.bag_units.find_unit_same_region(zone_designed):
                self._canvas.application.label_dynamic_information.config(text="Création d'unité impossible : une unité occupe déjà cette région.")
                return

            self._canvas.application.label_dynamic_information.config(text=f"Création de {unit}.\nCliquez milieu pour changer son type.\nCliquez droit pour changer son rôle.")
            self._canvas.bag_units.add_unit(unit)

            # redraw canvas (not very optmized !)
            self._canvas.refresh()

        elif button_clicked is ButtonEnum.MIDDLE_BUTTTON:
            # Purpose of this button is change unit type

            if self._zone_designed is None:
                self._canvas.application.label_dynamic_information.config(text="Désignez une zone.")
                return

            unit = self._canvas.bag_units.find_unit(self._zone_designed)
            if unit is None:
                self._canvas.application.label_dynamic_information.config(text="Désignez une unité.")
                return

            self._canvas.application.label_dynamic_information.config(text=f"Changement type d'unité de {unit} (ou suppression).")

            unit.type_unit = unit.type_unit.swap()
            if not unit.may_appear():
                self._canvas.application.label_dynamic_information.config(text="Changement refusé, une telle unité est possible à cet endroit")
                unit.type_unit = unit.type_unit.swap()
                return

            self._canvas.bag_units.add_unit(unit)

            # redraw canvas (not very optmized !)
            self._canvas.refresh()

        elif button_clicked is ButtonEnum.RIGHT_BUTTTON:
            # Purpose of this button is change unit role

            if self._zone_designed is None:
                self._canvas.application.label_dynamic_information.config(text="Désignez une zone.")
                return

            unit = self._canvas.bag_units.find_unit(self._zone_designed)
            if unit is None:
                self._canvas.application.label_dynamic_information.config(text="Désignez une unité.")
                return

            self._canvas.application.label_dynamic_information.config(text=f"Changement rôle de {unit}.")
            self._canvas.bag_units.remove_unit(unit)
            unit.role += 1
            nb_roles = data.VARIANT_DATA['roles']['number']
            if unit.role > nb_roles:
                unit.role = 1
            self._canvas.bag_units.add_unit(unit)

            # redraw canvas (not very optmized !)
            self._canvas.refresh()


class CentersEditionAutomaton(InputAutomaton):
    """ An automaton to edit center ownerships """

    def __init__(self, canvas: 'MyCanvas') -> None:

        self._canvas = canvas
        self._state = InputAutomatonStateEnum.STATE_INIT
        self._zone_designed: typing.Optional[int] = None

    def change_state(self, button_clicked: ButtonEnum, zone_designed: typing.Optional[int]) -> None:
        """ Make the automaton moves (actually this automatons stays in init state) """

        assert self._canvas.application is not None

        if button_clicked is ButtonEnum.LEFT_BUTTTON:
            # Purpose of this button is put center or not

            assert zone_designed is not None
            center_ownership = self._canvas.bag_centers.find_center(zone_designed)

            if zone_designed == self._zone_designed:
                if center_ownership is not None:
                    self._canvas.application.label_dynamic_information.config(text=f"Suppression de {center_ownership}.")
                    self._canvas.bag_centers.remove_center(center_ownership)

                    # redraw canvas (not very optmized !)
                    self._canvas.refresh()

                    self._zone_designed = None
                    return

            self._zone_designed = zone_designed

            if center_ownership is not None:
                self._canvas.application.label_dynamic_information.config(text=f"Sélection de {center_ownership}. Cliquez gauche pour supprimer cette possession.\nCliquez droit pour changer son rôle")
                return

            region_num = data.find_region_num(zone_designed)
            center_num = data.find_center_num(region_num)

            if center_num is None:
                self._canvas.application.label_dynamic_information.config(text="Cliquez sur une zone avec un centre")
                return

            center_ownership = ownerships.CenterOwnership(self._canvas, 1, center_num)

            self._canvas.application.label_dynamic_information.config(text=f"Création de {center_ownership}.\nCliquez gauche pour supprimer cette possession\nCliquez droit pour changer son rôle.")
            self._canvas.bag_centers.add_center(center_ownership)

            # redraw canvas (not very optmized !)
            self._canvas.refresh()

        elif button_clicked is ButtonEnum.RIGHT_BUTTTON:
            # Purpose of this button is change center role

            if self._zone_designed is None:
                self._canvas.application.label_dynamic_information.config(text="Désignez une zone.")
                return

            center_ownership = self._canvas.bag_centers.find_center(self._zone_designed)
            if center_ownership is None:
                self._canvas.application.label_dynamic_information.config(text="Désignez une zone avec un centre.")
                return

            self._canvas.application.label_dynamic_information.config(text=f"Changement de rôle de {center_ownership}.")
            self._canvas.bag_centers.remove_center(center_ownership)
            center_ownership.role += 1
            nb_roles = data.VARIANT_DATA['roles']['number']
            if center_ownership.role > nb_roles:
                center_ownership.role = 1
            self._canvas.bag_centers.add_center(center_ownership)

            # redraw canvas (not very optmized !)
            self._canvas.refresh()


class MyCanvas(tkinter.Canvas):
    """" A plotting capable canvas """

    def __init__(self, application: typing.Any, *args, **kwargs) -> None:  # type: ignore
        super().__init__(*args, **kwargs)

        self._application = application

        # click
        self.bind("<Button-1>", self.callback_click_mouse_left)
        self.bind("<Button-2>", self.callback_click_mouse_middle)
        self.bind("<Button-3>", self.callback_click_mouse_right)

        # places where we can click
        self._clickable_zones: typing.List[ClickableZone] = list()

        # the "bag" or forbiddens
        self._bag_forbiddens = forbiddens.BagForbiddens(self)

        # the "bag" or units
        self._bag_units = units.BagUnits(self)

        # the "bag" or orders
        self._bag_orders = orders.BagOrders(self)

        # the "bag" or centers
        self._bag_centers = ownerships.BagCenters(self)

        # automaton to receive orders/units/centers edition
        self._current_automaton: typing.Optional[InputAutomaton] = None

        # will be affected later
        self._image: typing.Optional[tkinter.PhotoImage] = None

    def reset(self) -> None:
        """ erase everything in canvas """
        self.delete("all")  # type: ignore

    def put_map(self) -> None:
        """ Put the map in canvas """

        # make image from file
        self._image = tkinter.PhotoImage(file=data.MAP_FILE)  # keep reference

        # check  size
        map_width = self._image.width()  # type: ignore
        map_height = self._image.height()  # type: ignore
        assert (map_width, map_height) == (IMPOSED_MAP_WIDTH, IMPOSED_MAP_HEIGHT), "Incorrect size for background image"

        # put the file
        self.create_image(0, 0, image=self._image, anchor='nw')  # type: ignore

    def put_names(self) -> None:
        """ Put names """

        # build the map and note clickable zones
        nb_regions = len(data.VARIANT_DATA['regions'])
        for region_num in range(1, nb_regions + 1):

            x_name = int(data.ZONE_DATA[str(region_num)]['x_name'])
            y_name = int(data.ZONE_DATA[str(region_num)]['y_name'])
            name = data.ZONE_DATA[str(region_num)]['name']
            self.create_text(x_name, y_name, text=name, font=(font.FONT_USED, font.FONT_SIZE))  # type: ignore
            clickable_zone = ClickableZone(x_name, y_name, CLICKABLE_ZONE_RADIUS, region_num)
            self.add_clickable_zone(clickable_zone)

            x_pos = int(data.ZONE_DATA[str(region_num)]['x_pos'])
            y_pos = int(data.ZONE_DATA[str(region_num)]['y_pos'])
            clickable_zone = ClickableZone(x_pos, y_pos, CLICKABLE_ZONE_RADIUS, region_num)
            self.add_clickable_zone(clickable_zone)

        offset = nb_regions
        for num, (region_num, coast_type_num) in enumerate(data.VARIANT_DATA['coastal_zones']):

            zone_num = offset + num + 1
            x_name = int(data.ZONE_DATA[str(zone_num)]['x_name'])
            y_name = int(data.ZONE_DATA[str(zone_num)]['y_name'])
            name = data.COAST_DATA[str(coast_type_num)]['name']
            self.create_text(x_name, y_name, text=name, font=(font.FONT_USED, font.FONT_SIZE))  # type: ignore
            clickable_zone = ClickableZone(x_name, y_name, CLICKABLE_ZONE_RADIUS, zone_num)
            self.add_clickable_zone(clickable_zone)

            x_pos = int(data.ZONE_DATA[str(zone_num)]['x_pos'])
            y_pos = int(data.ZONE_DATA[str(zone_num)]['y_pos'])
            clickable_zone = ClickableZone(x_pos, y_pos, CLICKABLE_ZONE_RADIUS, zone_num)
            self.add_clickable_zone(clickable_zone)

    def refresh(self) -> None:
        """ refresh whole canvas """

        self.reset()
        self.put_map()
        self.put_names()
        self.bag_forbiddens.refresh()
        self.bag_centers.refresh()
        self.bag_units.refresh()
        self.bag_orders.refresh()

    def find_zone(self, x_mouse: int, y_mouse: int) -> typing.Optional[int]:
        """ Finds which clickable zone matches """

        conflicts = set()
        for clickable in self._clickable_zones:
            if clickable.is_inside(x_mouse, y_mouse):
                identifier = clickable.identifier
                conflicts.add(identifier)
        if len(conflicts) != 1:
            return None
        return conflicts.pop()

    def add_clickable_zone(self, clickable_zone: ClickableZone) -> None:
        """ add clickable zone """
        self._clickable_zones.append(clickable_zone)

    def callback_click_mouse_left(self, event: typing.Any) -> None:
        """ left click on map occured """

        # if there  a clickable zone there ?
        zone_num = self.find_zone(event.x, event.y)
        if zone_num is None:
            assert self._application is not None
            self._application.label_dynamic_information.config(text="Pas de zone à cet endroit !")
            return

        assert self._current_automaton is not None
        self._current_automaton.change_state(ButtonEnum.LEFT_BUTTTON, zone_num)

    def callback_click_mouse_middle(self, _: typing.Any) -> None:
        """ middle click on map occured """

        assert self._current_automaton is not None
        self._current_automaton.change_state(ButtonEnum.MIDDLE_BUTTTON, None)

    def callback_click_mouse_right(self, _: typing.Any) -> None:
        """ right click on map occured """

        assert self._current_automaton is not None
        self._current_automaton.change_state(ButtonEnum.RIGHT_BUTTTON, None)

    @property
    def bag_forbiddens(self) -> forbiddens.BagForbiddens:
        """ property """
        return self._bag_forbiddens

    @property
    def bag_units(self) -> units.BagUnits:
        """ property """
        return self._bag_units

    @property
    def bag_orders(self) -> orders.BagOrders:
        """ property """
        return self._bag_orders

    @property
    def bag_centers(self) -> ownerships.BagCenters:
        """ property """
        return self._bag_centers

    @property
    def current_automaton(self) -> typing.Optional[InputAutomaton]:
        """ property """
        return self._current_automaton

    @current_automaton.setter
    def current_automaton(self, current_automaton: InputAutomaton) -> None:
        """ setter """
        self._current_automaton = current_automaton

    @property
    def application(self) -> typing.Any:
        """ property """
        return self._application


if __name__ == "__main__":
    assert False, "Do not run this script"
