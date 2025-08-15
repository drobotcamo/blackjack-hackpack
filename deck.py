import math
import random
from enum import Enum
from typing import List, Callable


# Represents a Suit.
class Suit:
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        if isinstance(other, Suit):
            return self.name == other.name
        return False


# Enumerated Type Representing the four possible suits that a card may have.
class Suits(Enum):
    HEARTS = Suit('♥')
    DIAMONDS = Suit('♦')
    CLUBS = Suit('♣')
    SPADES = Suit('♠')


# Represents a Rank with a name and a value
class Rank:
    def __init__(self, name: str, priority: int, score_value: int):
        self.name = name
        self.priority = priority
        self.score_value = score_value


# Enumerated Type that represents all the possible ranks that a card can be.
class Ranks(Enum):
    TWO = Rank('2', 2, 2)
    THREE = Rank('3', 3, 3)
    FOUR = Rank('4', 4, 4)
    FIVE = Rank('5', 5, 5)
    SIX = Rank('6', 6, 6)
    SEVEN = Rank('7', 7, 7)
    EIGHT = Rank('8', 8, 8)
    NINE = Rank('9', 9, 9)
    TEN = Rank('T', 10, 10)
    JACK = Rank('J', 11, 10)
    QUEEN = Rank('Q', 12, 10)
    KING = Rank('K', 13, 10)
    ACE = Rank('A', 14, 11)


class Card:
    static_id = 0

    def __init__(self, rank: Rank, suit: Suit):
        self.rank = rank
        self.suit = suit
        self.score_value  = rank.score_value
        self.id = Card.static_id
        self.flipped = False
        Card.static_id += 1

    def isFace(self) -> bool:
        if 10 < self.rank.priority < 14:
            return True
        return False

    @classmethod
    def from_card(cls, other_card):
        new = Card(Ranks.EIGHT.value, Suits.DIAMONDS.value)
        new.rank = other_card.rank
        new.suit = other_card.suit
        return new

    def __str__(self):
        return self.rank.name + " of " + self.suit.name # + " which scores for " + str(self.getScoringValue()) + " points"

    def __eq__(self, other):
        if isinstance(other, Card):
            return self.rank == other.rank and self.suit == other.suit
        return False

    def __copy__(self):
        newCard = Card(self.rank, self.suit)

    def getScoringValue(self) -> int:
        return self.scoringValue

    def flip(self):
        self.flipped = not self.flipped

    def ascii_art_coords(self) -> List[dict]:
        """
        Returns a list of dicts: {'symbol': str, 'x': int, 'y': int}
        representing the card as a 4x3 box with value and suit centered,
        using Unicode box-drawing characters.
        """
        # Unicode box-drawing characters
        TL = '┌'  # top-left
        TR = '┐'  # top-right
        BL = '└'  # bottom-left
        BR = '┘'  # bottom-right
        H  = '─'  # horizontal
        V  = '│'  # vertical

        value = self.rank.name if not self.flipped else "▓"
        suit = self.suit.name if not self.flipped else "▓"

        lines = [
            [TL, H, H, TR],
            [V, value, suit, V],
            [BL, H, H, BR]
        ]

        coords = []
        for y, line in enumerate(lines):
            for x, symbol in enumerate(line):
                coords.append({'symbol': symbol, 'x': x, 'y': y})
        return coords


class Deck:
    def __init__(self, ):
        self.base_cards: List[Card] = []
        for suit in Suits:
            for rank in Ranks:
                self.base_cards.append(Card(rank.value, suit.value))

        self.active_cards = self.base_cards.copy()


    def add(self, card: Card):
        self.base_cards.append(card)

    def remove(self, card_id: int):
        target_index = -1
        for index, card in enumerate(self.base_cards):
            print(f"{card.id}     {card_id}")
            if card.id == card_id:
                print(f"Found Bro! He is at {index}")
                print(card)
                target_index = index
                break
        self.base_cards.pop(target_index)

    def shuffle(self):
        # shuffle deck here
        new_deck = []
        options = list(self.base_cards)
        while len(new_deck) < len(self.base_cards):
            index = math.floor(random.randrange(0, len(options)))
            addition = options[index]
            new_deck.append(addition)
            options.remove(addition)

        self.active_cards = new_deck

    def draw(self, flipped=False) -> Card:
        card = self.active_cards.pop()
        if flipped:
            card.flip()
        return card

    def __str__(self) -> str:
        returnString = "Printing out deck:\n"
        for card in self.base_cards:
            returnString += str(card) + "\n"
        returnString += f"Size: {len(self.base_cards)} cards"

        returnString += "\nActive Cards:\n"
        for card in self.active_cards:
            returnString += str(card) + "\n"
        returnString += f"Size: {len(self.active_cards)} cards"

        returnString += "\n\n"
        returnString += "Deck ID: " + str(id(self)) + "\n"
        returnString += "Static ID: " + str(Card.static_id) + "\n"

        return returnString

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index < len(self.base_cards):
            result = self.base_cards[self.index]
            self.index += 1
            return result
        else:
            raise StopIteration


class Hand:
    def __init__(self, cards=None, handSize=8):
        self.handSize = handSize
        if cards:
            self.cards = cards.copy()
        else:
            self.cards = []

    def add_card(self, card: Card):
        self.cards.append(card)

    def copy(self):
        return Hand(cards=self.cards, handSize=self.handSize)

    def __str__(self) -> str:
        returnString = "Hand Contents:\n"
        for card in sorted(self.cards, key=lambda thisCard: thisCard.rank.priority, reverse=True):
            returnString += str(card) + "\t"
        return returnString

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index < len(self.cards):
            result = self.cards[self.index]
            self.index += 1
            return result
        else:
            raise StopIteration

    def discard(self, card: Card):
        self.cards.remove(card)
        return None

    def score(self):
        scoringHandType: HandType = None
        scoringHand: List[Card] = None
        for handType in HandTypes:
            validHand: List[Card] = handType.value.findHand(self.cards.copy())
            if validHand:
                scoringHandType = handType.value
                scoringHand = validHand
                break

        chips = scoringHandType.chips
        mult = scoringHandType.mult

        for card in scoringHand:
            chips += card.scoringValue

        value = chips * mult
        # print(f"Hand scored: {scoringHandType}, worth {value} chips")
        # print(f"Hand is:")
        # for card in scoringHand:
        #     print(str(card))
        return scoringHandType

    def empty(self):
        self.cards = []

    def containsFlushOfSize(self, size: int, suit: Suit) -> List[Card]:

        suitOccurences = {suit.value.name: [] for suit in Suits}

        for card in self.cards:
            if card.suit != None:
                suitOccurences[card.suit.name].append(card)

        flushSuit: Suit = None
        flush: List[Card] = []
        for suit in Suits:
            if len(suitOccurences[suit.value.name]) == size:
                for card in suitOccurences[suit.value.name]:
                    flushSuit = card.suit
                    flush.append(card)
                break

        return flush.copy()

    def returnLargestFlush(self) -> List[Card]:

        maxFlushSize = 0
        suitOccurrences = {suit.value.name: [] for suit in Suits}

        for card in self.cards:
            if card.suit is not None:
                suitOccurrences[card.suit.name].append(card)

        flushSuit: Suit or None = None
        flush: List[Card] = []
        for suit in Suits:
            if len(suitOccurrences[suit.value.name]) > maxFlushSize:
                flush.clear()
                maxFlushSize = len(suitOccurrences[suit.value.name])
                for card in suitOccurrences[suit.value.name]:
                    flushSuit = card.suit
                    flush.append(card)

        return flush.copy()


class HandType:
    def __init__(self, chips: int, mult: int, findHand: Callable[[List[Card]], List[Card]], name: str):
        self.chips = chips
        self.mult = mult
        self.level = 1
        self.findHand = findHand
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other):
        if isinstance(other, HandType):
            return self.name == other.name
        return False


class HandTypes(Enum):
    def findHighCard(hand: List[Card]) -> List[Card]:
        high_card_value = 1
        high_card = None
        for card in hand:
            if card.rank.priority > high_card_value:
                high_card_value = card.rank.priority
                high_card = Card.from_card(card)
        return [high_card]

    def findPair(hand: List[Card]) -> List[Card]:
        occurences = [[] for _ in range(15)]
        for card in hand:
            occurences[card.rank.priority].append(card)

        high_pair = []
        for i in range(0, len(occurences)):
            if len(occurences[i]) == 2:
                if high_pair == []:
                    high_pair = occurences[i]
                else:
                    if high_pair[0].rank.priority < occurences[i][0].rank.priority:
                        high_pair = occurences[i]

        return high_pair

    def findTwoPair(hand: List[Card]) -> List[Card]:
        occurences = [[] for _ in range(15)]
        for card in hand:
            occurences[card.rank.priority].append(card)

        pairs = []
        for i in range(0, len(occurences)):
            if len(occurences[i]) == 2:
                pairs.append(occurences[i].copy())
        pairs = sorted(pairs, key=lambda pair: pair[0].rank.priority)
        return [pairs[0][0], pairs[0][1], pairs[1][0], pairs[1][1]] if len(pairs) >= 2 else []

    def findThreeOfAKind(hand: List[Card]) -> List[Card]:
        occurences = [[] for _ in range(15)]
        for card in hand:
            occurences[card.rank.priority].append(card)

        high_threeOfAKind = []
        for i in range(0, len(occurences)):
            if len(occurences[i]) == 3:
                if high_threeOfAKind == []:
                    high_threeOfAKind = occurences[i]
                else:
                    if high_threeOfAKind[0].rank.priority < occurences[i][0].rank.priority:
                        high_threeOfAKind = occurences[i]

        return high_threeOfAKind

    def findFourOfAKind(hand: List[Card]) -> List[Card]:
        occurences = [[] for _ in range(15)]
        for card in hand:
            occurences[card.rank.priority].append(card)

        high_fourOfAKind: List[Card] = []
        for i in range(0, len(occurences)):
            if len(occurences[i]) == 4:
                if high_fourOfAKind == []:
                    high_fourOfAKind = occurences[i]
                else:
                    if high_fourOfAKind[0].rank.priority < occurences[i][0].rank.priority:
                        high_fourOfAKind = occurences[i]

        return high_fourOfAKind

    def findFullHouse(hand: List[Card]) -> List[Card]:
        highFullHouse = []

        occurences = [[] for _ in range(15)]
        for card in hand:
            occurences[card.rank.priority].append(card)

        high_threeOfAKind = []
        for i in range(0, len(occurences)):
            if len(occurences[i]) == 3:
                if high_threeOfAKind == []:
                    high_threeOfAKind = occurences[i]
                    newHand = hand.copy()
                    for card in high_threeOfAKind:
                        newHand.remove(card)
                    pair = HandTypes.findPair(newHand)
                    if pair != []:
                        highFullHouse = []
                        for card in high_threeOfAKind:
                            highFullHouse.append(card)
                        for card in pair:
                            highFullHouse.append(card)
                else:
                    if high_threeOfAKind[0].rank.priority < occurences[i][0].rank.priority:
                        high_threeOfAKind = occurences[i]
                        newHand = hand.copy()
                        for card in high_threeOfAKind:
                            newHand.remove(card)
                        pair = HandTypes.findPair(newHand)
                        if pair:
                            highFullHouse = []
                            for card in high_threeOfAKind:
                                highFullHouse.append(card)
                            for card in pair:
                                highFullHouse.append(card)

        return highFullHouse

    def findStraight(hand: List[Card]) -> List[Card]:
        if len(hand) < 5:
            return []

        hand = sorted(hand, key=lambda card: card.rank.priority)

        highestStraightTopValue = 0
        straight: List[Card] = [hand[0]]
        highestStraight: List[Card] = []

        straightLength = 1
        straightCursor = hand[0].rank.priority
        for index in range(1, len(hand)):
            if hand[index].rank.priority == straightCursor + 1:
                straight.append(hand[index])
                straightLength += 1
                straightCursor += 1
                if straightLength == 5:
                    # and hand[index - 5].rank.value > hand[highgestStraightStartIndex].rank.value
                    if hand[index].rank.priority > highestStraightTopValue:
                        highestStraightTopValue = hand[index].rank.priority
                        highestStraight = straight.copy()
            elif hand[index].rank.priority == straightCursor:
                continue
            else:
                straightLength = 1
                straightCursor = hand[index].rank.priority
                straight = [hand[index]]

        return highestStraight

    def findFlush(hand: List[Card]) -> List[Card]:
        suits = {suit.value.name: [] for suit in Suits}
        for card in hand:
            suits[card.suit.name].append(card)

        for suit, cards in suits.items():
            if len(cards) >= 5:
                return sorted(cards, key=lambda card: card.rank.priority, reverse=True)[:5]
        return []

    def findStraightFlush(hand: List[Card]) -> List[Card]:
        highestStraightFlushValue = 0
        highestStraightFlush = []
        suits = {suit.value.name: [] for suit in Suits}
        for card in hand:
            suits[card.suit.name].append(card)

        for suit, cards in suits.items():
            if len(cards) >= 5:
                straightFlush = HandTypes.findStraight(
                    sorted(cards, key=lambda card: card.rank.priority, reverse=True)[:5])
                if straightFlush != [] and straightFlush[4].rank.priority > highestStraightFlushValue:
                    highestStraightFlushValue = straightFlush[4].rank.priority
                    highestStraightFlush = straightFlush
        return highestStraightFlush

    STRAIGHT_FLUSH = HandType(100, 8, findStraightFlush, "Straight Flush")
    FOUR_OF_A_KIND = HandType(60, 7, findFourOfAKind, "Four of a Kind")
    FULL_HOUSE = HandType(40, 4, findFullHouse, "Full House")
    FLUSH = HandType(35, 4, findFlush, "Flush")
    STRAIGHT = HandType(30, 4, findStraight, "Straight")
    THREE_OF_A_KIND = HandType(30, 3, findThreeOfAKind, "Three of a Kind")
    TWO_PAIR = HandType(20, 2, findTwoPair, "Two Pair")
    PAIR = HandType(10, 2, findPair, "Pair")
    HIGH_CARD = HandType(5, 1, findHighCard, "High Card")
