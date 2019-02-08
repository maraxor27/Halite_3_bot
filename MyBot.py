import hlt
from hlt import constants, commands, entity
from hlt.positionals import Direction, Position
import logging
import time
import queue


class ClosterMap:
    closter_graph = {}
    closter_list = []
    halite_threshold = 0
    closters_pos_list = []
    closters_pos_dict = {}
    average_halite = 0
    ecart_type = 0
    def __init__(self):
        logging.info("init")
        self.closterGraph()
        self.findAverageHalite()
        self.ecart_type = self.ecartType(self.halite_pos_list)
        self.halite_threshold = self.threshold_calculator()
        logging.info("halite threshold = {} , average halite = {} , ecart type = {}"
                     .format(self.halite_threshold, self.average_halite, self.ecart_type))
        self.closter_list = []
        self.defineClosters_2()
        self.closter_list.sort()
        self.ennemyPos = self.findEnnemyDropOff()
        return

    def update(self):
        update_time_1 = time.perf_counter()
        logging.info("update")
        self.findAverageHalite()
        self.ecart_type = self.ecartType(self.halite_pos_list)
        self.halite_threshold = self.threshold_calculator()
        for closter in self.closter_list:
            if len(closter.pos_list) < ClosterClass.min_size:
                for ship_id in closter.ship_id_list:
                    ship_id_status[ship_id] = "nothing"
                self.closter_list.remove(closter)
            else:
                closter.update()
        self.defineClosters_2()
        self.closter_list.sort()
        update_time_2 = time.perf_counter()
        logging.warning("it took {} seconds to update closter_map".format(update_time_2 - update_time_1))
        return

    def threshold_calculator(self):
        if self.ecart_type < 50:
            return 2/3 * self.average_halite
        else:
            return 2/3 * self.average_halite + 2/3 * self.ecart_type

    def findAverageHalite(self):
        self.total_halite = 0
        self.halite_pos_list = []
        for x in range(0, game_map.width):
            for y in range(0, game_map.height):
                self.total_halite += game_map[Position(x, y)].halite_amount
                self.halite_pos_list.append(game_map[Position(x, y)].halite_amount)

        self.average_halite = self.total_halite / (game_map.width * game_map.height)
        return

    def ecartType(self, l):
        a = 0
        for x in l:
            a += x
        a = a / len(l)
        somme = 0
        for x in l:
            somme += (x - a) ** 2
        s = (somme / (len(l) - 1)) ** (1 / 2)
        return s

    def defineClosters(self):
        '''
        checks every position in the game map and creates closter
        :return:
        '''
        for x in range(0, game_map.width):
            for y in range(0, game_map.height):
                if game_map[Position(x, y)].halite_amount >= self.halite_threshold and \
                        (x, y) not in self.closters_pos_list:
                    closter = ClosterClass(Position(x, y), self.halite_threshold)
                    if len(closter.pos_list) > 0:
                        self.closters_pos_list.append((x, y))
                        self.closter_list.append(closter)
        return

    def defineClosters_2(self):
        threshold_list = [1000, 900, 800, 400, 200, 50, 1] #[1000, 900, 800, 400, 200, 100, 50, 1]
        for threshold in threshold_list:
            for x in range(0, game_map.width):
                for y in range(0, game_map.height):
                    if game_map[Position(x, y)].halite_amount >= threshold and \
                            self.closters_pos_dict.get((x, y)) == None:
                        closter = ClosterClass(Position(x, y), threshold)
                        if len(closter.pos_list) > 1:
                            self.closters_pos_dict[(x, y)] = 1
                            self.closter_list.append(closter)
        return

    def closterGraph(self):
        '''
        Makes a graph of the game map in a way that each position is connected to the four position at a distance of one unit
        for example: position (0, 0) is connected to (1, 0), (-1, 0), (0, 1), (0, -1)
        :return:
        '''
        for x in range(0, game_map.width):
            for y in range(0, game_map.height):
                list_move = []
                list_move.append(((x + 1) % game_map.width, y))
                list_move.append(((x - 1) % game_map.width, y))
                list_move.append((x, (y + 1) % game_map.height))
                list_move.append((x, (y - 1) % game_map.height))
                self.closter_graph[(x, y)] = list_move
        return

    def nearestStructure(self, position):
        distance = game_map.calculate_distance(position, me.shipyard.position)
        drop_off_position = me.shipyard.position
        for drop_off in me.get_dropoffs():
            distance2 = game_map.calculate_distance(position, drop_off.position)
            if distance2 < distance:
                distance = distance2
                drop_off_position = drop_off.position
        for ennemy in self.ennemyPos:
            distance2 = game_map.calculate_distance(position, ennemy.pos)
            if distance2 <= distance:
                distance = distance2
                drop_off_position = ennemy.pos
        return drop_off_position

    def nearestDropOff(self, position):
        '''
        Finds the nearest drop off or shipyard to the position given
        :param position:
        :return:
        '''
        distance = game_map.calculate_distance(position, me.shipyard.position)
        drop_off_position = me.shipyard.position
        for drop_off in me.get_dropoffs():
            distance2 = game_map.calculate_distance(position, drop_off.position)
            if distance2 < distance:
                distance = distance2
                drop_off_position = drop_off.position
        return drop_off_position

    def distance(self, a, b):
        return min(abs(a.x - b.x), abs(b.x + game_map.width - a.x)) + \
               min(abs(a.y - b.y), abs(b.y + game_map.height - a.y))

    def findEnnemyDropOff(self):
        ennemyPos = []
        for x in range(0, game_map.width):
            for y in range(0, game_map.height):
                if game_map[Position(x, y)].has_structure:
                    logging.info("structure found")
                    if me.shipyard.position.x != x or me.shipyard.position.y != y:
                        logging.info("ennemy structure found")
                        ennemy = ShipyardBlock(Position(x, y))
                        ennemyPos.append(ennemy)
        return ennemyPos


class ClosterClass(ClosterMap):
    closter_max_size = 30
    closter_merge_size = 5
    min_halite = 10
    min_size = 2
    halite = 0
    has_dropoff = False

    def __init__(self, init_pos, halite_threshold):
        # self.closter_max_size = game_map.height % 10 * 2
        self.halite_threshold = halite_threshold
        self.init_pos = (init_pos.x, init_pos.y)
        self.pos_list = [self.init_pos]
        self.halite = game_map[Position(init_pos.x, init_pos.y)].halite_amount
        self.expandCloster()
        if self.size > 1:
            self.ship_id_list = []
            self.distance = self.calculDistanceToDropOff()
            self.value = self.valueCalculator()
            self.use_cell = []
            self.max_ship = round(2 * self.size / 3)
            #logging.info("self.distance = {}, self.total_halite = {}, self.pos_list = {}"
            #             .format(self.distance, self.halite, self.pos_list))
            if self.size < self.max_ship:
                self.max_ship = self.size

    def __repr__(self):
        return "Closter [Value = {}, Halite = {}, Size = {}, ship_id_list = {}]"\
            .format(self.value, self.halite, self.size, self.ship_id_list)

    def __lt__(self, other):
        return self.value < other.value

    def valueCalculator(self):
        d_const = 0.1
        n_pos = len(self.pos_list)
        value_list = []
        if n_pos == 0:
            n_pos = 1
        n_ship = len(self.ship_id_list)
        if n_ship == 0:
            n_ship = 1
        totalValue = 0
        nearest_dropoff = self.nearestDropOff(Position(self.pos[0], self.pos[1]))
        for pos in self.pos_list:
            position = Position(pos[0], pos[1])
            distance = game_map.calculate_distance(nearest_dropoff, position)
            value = game_map[position].halite_amount / (d_const * distance ** 1.4 + (1 - d_const)) / (0.1 * n_ship + 0.9) #** (1 / 4)
            totalValue += round(value)
            value_list.append(value)
        if len(value_list) > 1:
            ecart = self.ecartType(value_list)
        else:
            ecart = 0
        return totalValue / n_pos + ecart
        ## return self.average_halite / (d_const * self.distance ** 1.3 + 1)
        ## return self.average_halite / (game_map.height * d_const * self.distance ** (1.1) + (1 - d_const))
        # return self.average_halite / self.distance ** (1/4)
        ## return self.average_halite - (self.average_halite*0.0125*self.distance)
        ## return self.average_halite - 0.8 * self.average_halite*self.distance / game_map.height

    def thresholdCalculator(self, x, distance):
        if distance == 0:
            return x
        else:
            return x # * (-1 / (15 * distance) + 1)

    def expandCloster(self):
        '''
        start at the origin and checks the point arround to make a region of point that are valuable
        :return:
        '''
        frontier = queue.PriorityQueue()
        frontier.put(self.init_pos, 0)
        came_from = {}
        self.frontier_list = []
        came_from[self.init_pos] = None
        cost_so_far = {}
        cost_so_far[self.init_pos] = 0
        self.size = 1
        while not frontier.empty() and self.size <= self.closter_max_size:
            current = frontier.get()
            # self.frontier_list.append(next)
            for next in self.closter_graph[current]:
                new_cost = cost_so_far[current] + (1000 - game_map[Position(current[0], current[1])].halite_amount)
                # The closter isn't to big, next position isn't
                # already in the closter, next position isn't in an other closter
                if self.size <= self.closter_max_size and \
                        game_map[Position(next[0], next[1])].halite_amount >= \
                        self.halite_threshold and \
                        (next not in came_from or new_cost < cost_so_far[next]) and \
                        self.closters_pos_dict.get(next) == None:
                    cost_so_far[next] = new_cost
                    priority = new_cost
                    frontier.put(next, priority)
                    came_from[next] = current
                    self.closters_pos_dict[next] = 1
                    self.pos_list.append(next)
                    self.size += 1
                    self.halite += game_map[Position(current[0], current[1])].halite_amount
        self.average_halite = round(self.halite / self.size)
        return

    def update(self):
        self.use_cell = []
        self.halite = 0
        for pos in self.pos_list:
            if game_map[Position(pos[0], pos[1])].halite_amount < self.halite_threshold / 10:
                if pos in self.pos_list:
                    self.pos_list.remove(pos)
                if pos in self.closters_pos_dict.keys():
                    self.closters_pos_dict.pop(pos)
            else:
                self.halite += game_map[Position(pos[0], pos[1])].halite_amount
        self.size = len(self.pos_list)
        if self.size >= self.min_size:
            self.average_halite = self.halite / self.size
            if self.size < self.max_ship:
                self.max_ship = round(2 * self.size / 3)
            self.valueUpdate()
        return

    def valueUpdate(self):
        if len(self.ship_id_list) != self.max_ship:
            self.value = self.valueCalculator()
        else:
            self.value = 0
        return

    def addShip(self, ship):
        for bateau_id in self.ship_id_list:
            if ship.id == bateau_id:
                return
        self.ship_id_list.append(ship.id)
        return

    def removeShip(self, ship):
        for bateau_id in self.ship_id_list:
            if bateau_id == ship.id:
                self.ship_id_list.remove(ship.id)
                return
        return

    def calculDistanceToDropOff(self):
        '''
        find the center of the positions
        find the nearest drop off from the center
        :return:
        '''
        pos_x = 0
        pos_y = 0
        for pos in self.pos_list:
            pos_x += pos[0]
            pos_y += pos[1]
        self.pos = (round(pos_x / len(self.pos_list)), round(pos_y / len(self.pos_list)))
        self.drop_off_pos = self.nearestDropOff(Position(self.pos[0], self.pos[1]))
        self.distance_from_drop_off = abs(self.distance(Position(self.pos[0], self.pos[1]), self.drop_off_pos))
        return self.distance_from_drop_off

    def isFull(self):
        if self.max_ship - 1 == len(self.ship_id_list):
            return True
        return False


class ShipyardBlock(ClosterMap):
    def __init__(self, pos):
        self.pos = pos
        self.status = "waiting for ship"
        self.the_ship = None
        self.nShipSent = 0
        logging.info("ennemy shipyard at {}".format(self.pos))

    def useShip(self, ship_id):
        self.the_ship = ship_id
        return

    def isBlocked(self):
        ship = all_ship_dict.get(self.the_ship)
        if ship is not None:
            return ship.position == self.pos
        else:
            return False

    def __repr__(self):
        return "shipyardBlock: [pos: {}  ship: {}]".format(self.pos, self.the_ship)


def bestLocation(ship, pos_list, use_cell):
    logging.info("best Location \nship: {}, pos_list: {}, use_cell before assigning ship: {}".format(ship, pos_list, use_cell))
    best_value = -1
    best_value_pos = None
    for pos in pos_list:
        value = game_map[Position(pos[0], pos[1])].halite_amount / (ClosterMap.distance(closter_map, ship.position, Position(pos[0], pos[1])) * 0.2 + 0.8)
        if value >= best_value and pos not in use_cell:
            best_value = value
            best_value_pos = pos
    if best_value_pos is None:
        return None
    else:
        use_cell.append(best_value_pos)
        return Position(best_value_pos[0], best_value_pos[1])


def possible_choices(pos_a, pos_b):
    '''
    :param pos_a:
    :param pos_b:
    :return: choices
    '''
    pos_a = game_map.normalize(pos_a)
    pos_b = game_map.normalize(pos_b)
    choices = []
    ax, ay, bx, by = pos_a.x, pos_a.y, pos_b.x, pos_b.y
    if bx < ax:
        if ax - bx < bx + game_map.width - ax:
            # west
            choices.append((-1, 0))
        elif ax - bx > bx + game_map.width - ax:
            # east
            choices.append((1, 0))
        elif ax - bx == bx + game_map.width - ax:
            # east and west
            choices.append((1, 0))
            choices.append((-1, 0))

    elif bx > ax:
        if bx - ax < ax + game_map.width - bx:
            # east
            choices.append((1, 0))
        elif bx - ax > ax + game_map.width - bx:
            # west
            choices.append((-1, 0))
        elif bx - ax == ax + game_map.width - bx:
            # east and west
            choices.append((1, 0))
            choices.append((-1, 0))
    elif ax == bx:
        pass

    if by < ay:
        if ay - by < by + game_map.height - ay:
            # north
            choices.append((0, -1))
        elif ay - by > by + game_map.height - ay:
            # south
            choices.append((0, 1))
        elif ay - by == by + game_map.height - ay:
            # north and south
            choices.append((0, -1))
            choices.append((0, 1))
    elif ay < by:
        if by - ay < ay + game_map.height - by:
            # south
            choices.append((0, 1))
        elif by - ay > ay + game_map.height - by:
            # north
            choices.append((0, -1))
        elif by - ay == ay + game_map.height - by:
            # north and south
            choices.append((0, -1))
            choices.append((0, 1))
    elif ay == by:
        pass

    return choices
# return choices over the form of (x, y) move ex.: (0, 1) for east


def mapGraph():
    dict_position = {}
    for x in range(0, game_map.width):
        for y in range(0, game_map.height):
            list_move = []
            coordinate = game_map.normalize(Position(x + 1, y))
            # if not game_map[coordinate].is_occupied:
            list_move.append((coordinate.x, coordinate.y))
            coordinate = game_map.normalize(Position(x - 1, y))
            # if not game_map[coordinate].is_occupied:
            list_move.append((coordinate.x, coordinate.y))
            coordinate = game_map.normalize(Position(x, y + 1))
            # if not game_map[coordinate].is_occupied:
            list_move.append((coordinate.x, coordinate.y))
            coordinate = game_map.normalize(Position(x, y - 1))
            # if not game_map[coordinate].is_occupied:
            list_move.append((coordinate.x, coordinate.y))
            dict_position[(x, y)] = list_move
    return dict_position


def remove_pos(pos, map_graph):
    pos = (pos.x, pos.y)
    for value in map_graph.values():
        if pos in value:
            value.remove(pos)
    return


def convert(move):
    if move == (1, 0):
        move = commands.EAST
    elif move == (-1, 0):
        move = commands.WEST
    elif move == (0, -1):
        move = commands.NORTH
    elif move == (0, 1):
        move = commands.SOUTH
    elif move == (0, 0):
        move = commands.STAY_STILL
    return move
# convert vector to command.direction


def check_ship_alive(ship_id):
    for bateau in me.get_ships():
        if bateau.id == ship_id:
            return True
    return False
# return true if ship exist in me.get_ships()


def allShipDict():
    all_ship_dict = {}
    for ship in me.get_ships():
        all_ship_dict[ship.id] = ship
    return all_ship_dict


def invertMove(move):
    if move == (0, 1):
        return (0, -1)
    elif move == (0, -1):
        return (0, 1)
    elif move == (1, 0):
        return (-1, 0)
    elif move == (-1, 0):
        return (1, 0)


def recursiveMove_part_2(move, next_position):
    global used_ship_move
    global not_moving_ship
    global not_moving_ship_move
    global all_ship_dict
    logging.info("next position is {}".format(next_position))

    if game_map[next_position].is_occupied:
        next_ship = game_map[next_position].ship
    else:
        next_ship = None
        logging.info("ship should be = None")

    if next_ship is None and no_go_position.get((next_position.x, next_position.y)) == None:
        return True
    elif next_ship is not None and next_ship.id in not_moving_ship and next_ship.id not in used_ship_move.keys() and \
            no_go_position.get((next_position.x, next_position.y)) == None:
        if move in not_moving_ship_move[next_ship.id]:
            logging.info("next_ship = {} and move is = {}".format(next_ship, move))
            if recursiveMove_part_2(move, next_ship.position.directional_offset(move)):
                used_ship_move[next_ship.id] = [move]
                not_moving_ship.remove(next_ship.id)
                not_moving_ship_move.pop(next_ship.id)
                pos = next_ship.position.directional_offset(move)
                no_go_position[(pos.x, pos.y)] = 1
                command_queue.append(next_ship.move(convert(move)))
                logging.info("{} is moving from {} to {}".format(next_ship, next_position, pos))
                return True

    elif next_ship is not None and next_ship.id in used_ship_move.keys() and \
            no_go_position.get((next_position.x, next_position.y)) != 1:
        if move in used_ship_move[next_ship.id]:
            return True
    return False


def recursiveMove_part_1():
    global used_ship_move
    global not_moving_ship
    global not_moving_ship_move
    global all_ship_dict
    iterator = 0
    while iterator < len(not_moving_ship_move.keys()):
        ship_id = not_moving_ship[iterator]
        ship = all_ship_dict.get(ship_id)
        if ship_id not in used_ship_move.keys():
            current_ship = all_ship_dict.get(ship_id)
            for move in not_moving_ship_move.get(current_ship.id):
                if move in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    going_2_position = current_ship.position.directional_offset(move)
                    going_2_pos = (going_2_position.x, going_2_position.y)
                    if no_go_position.get(going_2_pos) == None:
                        if recursiveMove_part_2(move, going_2_position):
                            used_ship_move[ship_id] = [move]
                            not_moving_ship.remove(current_ship.id)
                            not_moving_ship_move.pop(current_ship.id)
                            pos = ship.position.directional_offset(move)
                            no_go_position[(pos.x, pos.y)] = 1
                            command_queue.append(current_ship.move(convert(move)))
                            logging.info("{} is moving from {} to {}".format(ship, ship.position, pos))

                            break
        iterator += 1
    return


def neverMove(ship, dropoff=False):
    global command_queue
    global used_ship_move
    global no_go_position
    global dropoff_status
    global n_dropOff_created
    global making_dropOff_turn
    logging.info("ship {} will not move this turn".format(ship.id))
    used_ship_move[ship.id] = [(0, 0)]
    no_go_position[(ship.position.x, ship.position.y)] = 1
    game_map[ship.position].mark_unsafe(ship)
    if dropoff and me.halite_amount > constants.DROPOFF_COST:
        command_queue.append(ship.make_dropoff())
        n_dropOff_created += 1
        logging.info("n_dropOff_created: {}".format(n_dropOff_created))
        dropoff_status = None
        making_dropOff_turn = True
        logging.info("making a drop of this turn: {}".format(making_dropOff_turn))
    elif dropoff and not me.halite_amount <= constants.DROPOFF_COST:
        dropoff_status = "waiting for halite"
    elif not dropoff:
        command_queue.append(ship.move(convert((0, 0))))
    return


def willMove(ship, next_move, next_pos):
    global used_ship_move
    global command_queue
    global no_go_position
    logging.info("ship {} moving {} to go at {}".format(ship.id, next_move, next_pos))
    used_ship_move[ship.id] = [next_move]
    command_queue.append(ship.move(convert(next_move)))
    game_map[ship.position.directional_offset(next_move)].mark_unsafe(ship)
    no_go_position[(next_pos.x, next_pos.y)] = 1
    game_map[ship.position].mark_unsafe(ship)
    return


def notMove(ship, directions):
    global not_moving_ship
    global not_moving_ship_move
    logging.info("ship {} can't move for now".format(ship.id))
    logging.info("Only move possible: {}".format(directions))
    not_moving_ship_move[ship.id] = directions
    not_moving_ship.append(ship.id)
    game_map[ship.position].mark_unsafe(ship)
    return


def moveNow(ship, target, type, end = False, closter=None):
    global used_ship_move
    global not_moving_ship
    global not_moving_ship_move
    if type == "more":
        nHalite = -1

    elif type == "less":
        nHalite = 10000

    if ship.id not in used_ship_move.keys():
        directions = possible_choices(ship.position, target)
        next_move = (0, 0)
        for direction in directions:
            target_pos = ship.position.directional_offset(direction)
            target_coord = (target_pos.x, target_pos.y)
            if type == "less":
                next_pos_halite = game_map[target_pos].halite_amount
                if end and game_map[target_pos].has_structure:
                    next_move = direction
                    next_pos = target_pos
                    break
                elif next_pos_halite <= nHalite and not game_map[target_pos].is_occupied:
                    nHalite = next_pos_halite
                    next_move = direction
                    next_pos = target_pos
                elif game_map[target_pos].has_structure and game_map[target_pos].is_occupied:
                    otherShip = game_map[target_pos].ship
                    if otherShip is not None:
                        if not me.has_ship(otherShip.id):
                            next_move = direction
                            next_pos = target_pos
                            break
            elif type == "more":
                next_pos_halite = game_map[target_pos].halite_amount
                if next_pos_halite > nHalite and not game_map[target_pos].is_occupied:
                    nHalite = next_pos_halite
                    next_move = direction
                    next_pos = target_pos

        if next_move in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            ship_pos_halite = game_map[ship.position].halite_amount
            if type == "more":
                # moving
                movingCondition_1 = next_pos_halite / 25 - ship_pos_halite / 10 >= ship_pos_halite / 25
                movingCondition_2 = closter.average_halite / 25 - ship_pos_halite / 10 >= ship_pos_halite / 25
                if movingCondition_1 or movingCondition_2:
                    willMove(ship, next_move, next_pos)
                    return
                # not worth to move
                else:
                    neverMove(ship)
                    return
            elif type == "less" and not end:
                movingCondition_1 = next_pos_halite / 25 - ship_pos_halite / 10 > ship_pos_halite / 25
                if movingCondition_1 or 1000 >= ship_pos_halite / 25 + ship.halite_amount or \
                        game_map[next_pos].has_structure or ship.halite_amount >= 975:
                    willMove(ship, next_move, next_pos)
            # moving
            elif type == "less" and end:
                willMove(ship, next_move, next_pos)
        # can't move for now
        elif next_move == (0, 0):
            notMove(ship, directions)
    return


def assignBlockShipyard(ship, ship_id_status, closter_map):
    for ennemy in closter_map.ennemyPos:
        if not ennemy.isBlocked() and ennemy.status == "waiting for ship":
            ennemy.useShip(ship.id)
            ennemy.status = "has ship"
            ship_id_status[ship.id] = "block shipyard"
    return


def assignDropOff(ship, ship_id_status, closter_map):
    global dropoff_status
    closter_list = closter_map.closter_list
    closter_list.sort()
    iterator = 1
    min_distance = 10
    ennemyStructure = False
    while iterator < len(closter_list) + 1 and dropoff_status is None:
        closter = closter_list[0 - iterator]
        logging.info("condition: {} {} {}".format(closter.average_halite > 350, len(closter.ship_id_list) >= 1, len(closter.pos_list) >= 3))
        logging.info("condition value {} {}".format(closter.average_halite, closter.pos_list))
        if closter.average_halite > 350 and len(closter.ship_id_list) >= 3 and len(closter.pos_list) >= 3: # and not closter.has_dropoff:
            closter_position = Position(closter.pos[0], closter.pos[1])
            structurePosition = closter_map.nearestStructure(closter_position)
            for ennemy in closter_map.ennemyPos:
                if structurePosition == ennemy.pos:
                    ennemyStructure = True
            distance = game_map.calculate_distance(closter_position, closter_map.nearestStructure(closter_position))
            logging.info("maxdistance: {}, distance: {}, mindistance: {}")
            if maxDistanceDropOff() >= distance >= minDistanceDropOff(ennemy=ennemyStructure):
                logging.info("creating a dropoff")
                closter.addShip(ship)
                ship_id_status[ship.id] = "drop off"
                dropoff_status = "drop off found"
        iterator += 1
    return


def assignCloster(ship, ship_id_status, closter_map):
    closter_list = closter_map.closter_list
    closter_list.sort()
    iterator = 1
    if game.turn_number < 50:
        while iterator < len(closter_list) + 1 and ship_id_status.get(ship.id) == "nothing":
            closter = closter_list[0 - iterator]
            if not closter.isFull() and closter.distance < reachForTurn(50) and closter.average_halite > 100 and closter.size >= 3:
                closter.addShip(ship)
                ship_id_status[ship.id] = "searching halite"
                return
            iterator += 1
    if game.turn_number < 100:
        while iterator < len(closter_list) + 1 and ship_id_status.get(ship.id) == "nothing":
            closter = closter_list[0 - iterator]
            if not closter.isFull() and closter.distance < reachForTurn(100) and closter.average_halite > 100:
                closter.addShip(ship)
                ship_id_status[ship.id] = "searching halite"
                return
            iterator += 1
    while iterator < len(closter_list) + 1 and ship_id_status.get(ship.id) == "nothing":
        closter = closter_list[0 - iterator]
        if not closter.isFull():
            closter.addShip(ship)
            ship_id_status[ship.id] = "searching halite"
            return
        iterator += 1


def shipAssignation(ships, ship_id_status, closter_map):
    for ship in ships:
        logging.info("assign ship {} a task".format(ship.id))
        if game_map[ship.position].has_structure or ship_id_status.get(ship.id) == "block shipyard":
            ship_id_status[ship.id] = "nothing"
            for closter in closter_map.closter_list:
                closter.removeShip(ship)
        if ship_id_status.get(ship.id) == "nothing":
            global dropoff_status
            # if len(closter_map.ennemyPos) == 1:
            #     if game.turn_number > 40:
            #          assignBlockShipyard(ship, ship_id_status, closter_map)
            #          logging.info("assignBlockShipyard finish")
            if constants.MAX_TURNS - 150 > game.turn_number > 120 and dropoff_status is None and \
                    n_dropOff_created < max_dropOff:
                assignDropOff(ship, ship_id_status, closter_map)
                logging.info("assignDropOff finish")
            if ship_id_status.get(ship.id) == "nothing":
                for closter in closter_map.closter_list:
                    closter.removeShip(ship)
                assignCloster(ship, ship_id_status, closter_map)
                logging.info("assignCloster finish")


def shipIdStatus_update(ship_id_status):
    for ship in me.get_ships():
        if ship_id_status.get(ship.id) is None:
            ship_id_status[ship.id] = "nothing"
    return


def switchShip(all_ship_dict, not_moving_ship_move, not_moving_ship, used_ship_move, closter_map):
    iterator = 0
    while iterator < len(not_moving_ship_move.keys()):
        init_ship = all_ship_dict.get(not_moving_ship[iterator])
        most_halite_ship = -1
        best_ship = None
        best_direction = None
        if init_ship is not None:
            if init_ship.id not in used_ship_move.keys():
                logging.info("trying to switch ship {} and the directions are {}"
                             .format(init_ship, not_moving_ship_move.get(init_ship.id)))
                for direction in not_moving_ship_move[init_ship.id]:
                    if direction in [(1, 0), (-1, 0), (0, 1), (0, 1)]:
                        flip_ship = game_map[init_ship.position.directional_offset(direction)].ship
                        if flip_ship is not None and flip_ship.id != init_ship.id:
                            logging.info("with ship {} and the directions are {}"
                                         .format(flip_ship, not_moving_ship_move.get(flip_ship.id)))
                            if flip_ship.id in not_moving_ship_move.keys() and flip_ship.id not in used_ship_move.keys() and \
                                    invertMove(direction) in not_moving_ship_move[flip_ship.id]:
                                if most_halite_ship < flip_ship.halite_amount:
                                    most_halite_ship = flip_ship.halite_amount
                                    best_ship = flip_ship
                                    best_direction = direction
                                # used_ship_move[init_ship.id] = direction
                                # used_ship_move[flip_ship.id] = invertMove(direction)
                                # if init_ship.id in not_moving_ship_move.keys():
                                #     not_moving_ship_move.pop(init_ship.id)
                                #     not_moving_ship.remove(flip_ship.id)
                                # if flip_ship.id in not_moving_ship_move.keys():
                                #     not_moving_ship_move.pop(flip_ship.id)
                                #     not_moving_ship.remove(init_ship.id)
                                # no_go_position[(init_ship.position.x, init_ship.position.y)] = 1
                                # no_go_position[(flip_ship.position.x, flip_ship.position.y)] = 1
                                # command_queue.append(flip_ship.move(convert(invertMove(direction))))
                                # command_queue.append(init_ship.move(convert(direction)))
                                # break
                if best_ship is not None and init_ship is not None and best_direction is not None:
                    logging.info("succesfull switch!\n with {} and {}".format(init_ship, best_ship))
                    used_ship_move[init_ship.id] = direction
                    used_ship_move[best_ship.id] = invertMove(direction)
                    if init_ship.id in not_moving_ship_move.keys():
                        not_moving_ship_move.pop(init_ship.id)
                    if init_ship.id in not_moving_ship:
                        not_moving_ship.remove(init_ship.id)
                    if best_ship.id in not_moving_ship_move.keys():
                        not_moving_ship_move.pop(best_ship.id)
                    if best_ship.id in not_moving_ship:
                        not_moving_ship.remove(best_ship.id)
                    no_go_position[(init_ship.position.x, init_ship.position.y)] = 1
                    no_go_position[(best_ship.position.x, best_ship.position.y)] = 1
                    command_queue.append(best_ship.move(convert(invertMove(best_direction))))
                    command_queue.append(init_ship.move(convert(best_direction)))
        iterator += 1
    return


def movingStatusModification(ship):
    nearest_structure = closter_map.nearestDropOff(ship.position)
    if game_map.calculate_distance(ship.position, nearest_structure) <= 5:
        if ship.halite_amount > 950:
            ship_id_status[ship.id] = "going back"
        elif ship.halite_amount < 100:
            ship_id_status[ship.id] = "searching halite"
    elif game_map.calculate_distance(ship.position, nearest_structure) <= 10:
        if ship.halite_amount > 950:
            ship_id_status[ship.id] = "going back"
        elif ship.halite_amount < 100:
            ship_id_status[ship.id] = "searching halite"
    else:
        if ship.halite_amount > 950:
            ship_id_status[ship.id] = "going back"
        elif ship.halite_amount < 100:
            ship_id_status[ship.id] = "searching halite"
    return


def maxDistanceDropOff():
    size = game_map.height
    logging.info("size: {}, ennemy number: {}".format(size, len(closter_map.ennemyPos)))
    if 3 > len(closter_map.ennemyPos) >= 1:
        if size >= 64:
            return 40
        elif size >= 56:
            return 34
        elif size >= 48:
            return 28
        elif size >= 40:
            return 26
        elif size >= 32:
            return 22
    if len(closter_map.ennemyPos) >= 3:
        if size >= 64:
            return 27
        elif size >= 56:
            return 27
        elif size >= 48:
            return 26
        elif size >= 40:
            return 24
        elif size >= 32:
            return 18


def defineMaxDropOff():
    size = game.game_map.height
    if 3 > len(closter_map.ennemyPos) >= 1:
        if size >= 64:
            return 3
        elif size >= 56:
            return 2
        elif size >= 46:
            return 2
        elif size >= 40:
            return 1
        elif size >= 32:
            return 1
    elif len(closter_map.ennemyPos) >= 3:
        if size >= 64:
            return 2
        elif size >= 56:
            return 2
        elif size >= 46:
            return 1
        elif size >= 40:
            return 1
        elif size >= 32:
            return 1


def reachForTurn(turn):
    size = game_map.height
    if 3 > len(closter_map.ennemyPos) >= 1:
        if size >= 64:
            if turn <= 50:
                return 30
            elif turn <= 100:
                return 40
        elif size >= 56:
            if turn <= 50:
                return 30
            elif turn <= 100:
                return 40
        elif size >= 48:
            if turn <= 50:
                return 25
            elif turn <= 100:
                return 35
        elif size >= 40:
            if turn <= 50:
                return 25
            elif turn <= 100:
                return 35
        elif size >= 32:
            if turn <= 50:
                return 20
            elif turn <= 100:
                return 30
    elif len(closter_map.ennemyPos) >= 3:
        if size >= 64:
            if turn <= 50:
                return 40
            elif turn <= 100:
                return 50
        elif size >= 56:
            if turn <= 50:
                return 35
            elif turn <= 100:
                return 40
        elif size >= 48:
            if turn <= 50:
                return 30
            elif turn <= 100:
                return 35
        elif size >= 40:
            if turn <= 50:
                return 25
            elif turn <= 100:
                return 30
        elif size >= 32:
            if turn <= 50:
                return 30
            elif turn <= 100:
                return 30


def stopNewShip():
    # average halite when to stop making new ship
    size = game.game_map.height
    if 3 > len(closter_map.ennemyPos) >= 1:
        if size >= 64:
            return 120
        elif size >= 56:
            return 110
        elif size >= 48:
            return 100
        elif size >= 40:
            return 80
        elif size >= 32:
            return 100
    elif len(closter_map.ennemyPos) >= 3:
        if size >= 64:
            return 120
        elif size >= 56:
            return 110
        elif size >= 48:
            return 100
        elif size >= 40:
            return 90
        elif size >= 32:
            return 90


def minDistanceDropOff(ennemy=False):
    size = game.game_map.height
    if not ennemy:
        if 3 > len(closter_map.ennemyPos) >= 1:
            if size >= 64:
                return 14
            elif size >= 56:
                return 13
            elif size >= 48:
                return 11
            elif size >= 40:
                return 10
            elif size >= 32:
                return 8
        elif len(closter_map.ennemyPos) >= 3:
            if size >= 64:
                return 13
            elif size >= 56:
                return 12
            elif size >= 48:
                return 11
            elif size >= 40:
                return 10
            elif size >= 32:
                return 8
    elif ennemy:
        if len(closter_map.ennemyPos) >= 1:
            if size >= 64:
                return 20
            elif size >= 56:
                return 18
            elif size >= 48:
                return 17
            elif size >= 40:
                return 16
            elif size >= 32:
                return 14
        elif len(closter_map.ennemyPos) >= 3:
            if size >= 64:
                return 19
            elif size >= 56:
                return 18
            elif size >= 48:
                return 17
            elif size >= 40:
                return 16
            elif size >= 32:
                return 15


game = hlt.Game()
# intialisation of variable
# list of closters
# a list of region with valuable positions
closter_list = []
# ship status
ship_id_status = {}
game.ready("Maraxor27")
logging.info("Maraaxor27")
# maximum number of drop off

n_dropOff_created = 0
n_dropoff_blocked = 0
dropoff_status = None

while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map
    command_queue = []
    all_ship_dict = allShipDict()
    shipIdStatus_update(ship_id_status)

    making_dropOff_turn = False
    no_go_position = {}
    used_ship_move = {}
    not_moving_ship = []
    not_moving_ship_move = {}

    if game.turn_number == 1:
        closter_map = ClosterMap()
        map_graph = mapGraph()
        max_dropOff = defineMaxDropOff()
    else:
        closter_map.update()

    shipAssignation(me.get_ships(), ship_id_status, closter_map)
    logging.info("shipAssignation finish")

    # moving ship to block ennemy
    for ennemy in closter_map.ennemyPos:
        if ennemy.status == "has ship":
            ship = all_ship_dict.get(ennemy.the_ship)
            if ship is not None:
                if ship.position == ennemy.pos:
                    neverMove(ship)
                elif (game_map[ship.position].halite_amount / constants.MOVE_COST_RATIO) <= ship.halite_amount or \
                        game_map[ship.position].has_structure:
                    moveNow(ship, ennemy.pos, "less")
                else:
                    neverMove(ship)
    logging.info("moving ship to block ennemy finish")

    logging.info("\nused_ship list: {}".format(used_ship_move))
    logging.info("not_moving_ship list: {}".format(not_moving_ship_move))
    logging.info("not_moving_ship list: {}\n".format(not_moving_ship_move))

    for ship in me.get_ships():
        logging.info("ship {} is doing {}".format(ship.id, ship_id_status[ship.id]))

    # moving for drop off, going back, searching halite
    for closter in closter_map.closter_list:
        for ship_id in closter.ship_id_list:
            ship = all_ship_dict.get(ship_id)
            if ship is not None and ship.id not in used_ship_move.keys():
                logging.info("\n\nmoving ship {}".format(ship.id))
                nearest_dropoff_position = closter_map.nearestDropOff(ship.position)
                if constants.MAX_TURNS - (game.turn_number + 10) <= game_map.calculate_distance(
                        ship.position, nearest_dropoff_position) or game.turn_number + 10 >= constants.MAX_TURNS:
                    if (game_map[ship.position].halite_amount / constants.MOVE_COST_RATIO) <= ship.halite_amount:
                        moveNow(ship, nearest_dropoff_position, "less", end=True)
                    else:
                        neverMove(ship)
                else:
                    logging.info("not end game")
                    if ship_id_status.get(ship.id) == "drop off":
                        if not making_dropOff_turn:
                            ennemyStructure = False
                            dropoff_position = Position(closter.pos[0], closter.pos[1])
                            structurePosition = closter_map.nearestStructure(dropoff_position)
                            for ennemy in closter_map.ennemyPos:
                                if structurePosition == ennemy.pos:
                                    ennemyStructure = True
                            if game_map.calculate_distance(dropoff_position, ship.position) <= 5:
                                dropoff_status = "waiting for halite"
                            if maxDistanceDropOff() >= game_map.calculate_distance(dropoff_position, nearest_structure) \
                                    >= minDistanceDropOff(ennemy=ennemyStructure) and \
                                    n_dropOff_created < max_dropOff and closter.average_halite >= 350:
                                if ship.position == dropoff_position:
                                    neverMove(ship, dropoff=True)
                                else:
                                    if (game_map[ship.position].halite_amount / constants.MOVE_COST_RATIO) <= \
                                            ship.halite_amount or game_map[ship.position].has_structure:
                                        moveNow(ship, dropoff_position, "less")
                                    else:
                                        neverMove(ship)
                            else:
                                #directions = [(1, 0), (-1, 0), (0, 1), (0, 1)]
                                ship_id_status[ship.id] = "searching halite"#"nothing"
                                #notMove(ship, directions)
                                dropoff_status == None
                        else:
                            ship_id_status[ship.id] = "searching halite"
                    else:
                        # random drop off
                        ship_count = 0
                        haliteRandDropOff = constants.SHIP_COST + constants.DROPOFF_COST
                        nearest_structure = closter_map.nearestDropOff(ship.position)
                        if constants.MAX_TURNS - 150 >= game.turn_number >= 150 and n_dropOff_created < max_dropOff and \
                            game_map.calculate_distance(ship.position, nearest_structure) >= 15 and \
                                dropoff_status != "waiting for halite" and me.halite_amount >= haliteRandDropOff and \
                                    not making_dropOff_turn:
                            ship_coord_x = ship.position.x
                            ship_coord_y = ship.position.y
                            for x in range(ship_coord_x - 5, ship_coord_x + 6):
                                for y in range(ship_coord_y - 5, ship_coord_y + 6):
                                    if game_map[Position(x, y)].is_occupied:
                                        ship_count += 1
                        if ship_count >= 12 and not making_dropOff_turn and game_map[ship.position].halite_amount > 350:
                            ship_id_status[ship.id] = "make a drop off"
                            neverMove(ship, dropoff=True)
                        else:
                            movingStatusModification(ship)
                            if ship_id_status.get(ship.id) == "searching halite":
                                logging.info("in searching halite mode")
                                if (game_map[ship.position].halite_amount / constants.MOVE_COST_RATIO) <= ship.halite_amount or \
                                        game_map[ship.position].has_structure:
                                    target = bestLocation(ship, closter.pos_list, closter.use_cell)
                                    if target is None:
                                        directions = [(1, 0), (-1, 0), (0, 1), (0, 1)]
                                        ship_id_status[ship.id] = "nothing"
                                        notMove(ship, directions)
                                    else:
                                        logging.info("ship {} is going to {}".format(ship.id, target))
                                        moveNow(ship, target, "more", closter=closter)
                                else:
                                    neverMove(ship)
                            elif ship_id_status.get(ship.id) == "going back":
                                logging.info("in going back mode")
                                if (game_map[ship.position].halite_amount / constants.MOVE_COST_RATIO) <= ship.halite_amount or \
                                        game_map[ship.position].has_structure:
                                    target = closter_map.nearestDropOff(ship.position)
                                    moveNow(ship, target, "less")
                                else:
                                    neverMove(ship)
    logging.info("moving for drop off, going back, searching halite finish")

    logging.info("\nused_ship list: {}".format(used_ship_move))
    logging.info("not_moving_ship list: {}".format(not_moving_ship_move))
    logging.info("no_go_position: {}".format(no_go_position))

    switchShip(all_ship_dict, not_moving_ship_move, not_moving_ship, used_ship_move, closter_map)
    logging.info("switchShip finish")

    recursiveMove_part_1()
    logging.info("recursiveMove finish")

    logging.info("dropoff_status is: {}".format(dropoff_status))
    if dropoff_status == "waiting for halite" or making_dropOff_turn:
        min_halite_base = constants.SHIP_COST + constants.DROPOFF_COST
    else:
        min_halite_base = constants.SHIP_COST

    if game_map[me.shipyard.position].ship is not None and me.halite_amount >= min_halite_base:
        if not me.has_ship(game_map[me.shipyard.position].ship.id):
            command_queue.append(me.shipyard.spawn())

    elif 4.2 * constants.MAX_TURNS / 8 > game.turn_number and me.halite_amount >= min_halite_base and \
            no_go_position.get((me.shipyard.position.x, me.shipyard.position.y)) is None: # and int(round(closter_map.average_halite)) > stopNewShip():
        logging.info("make a ship at {}".format(me.shipyard.position))
        command_queue.append(me.shipyard.spawn())

    game.end_turn(command_queue)