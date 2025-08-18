from the_ignition import *
from deck import *

def main():
    hand = BlackjackHand()
    hand.append(Card.from_string("A♥"))
    hand.append(Card.from_string("4♥"))
    hand.append(Card.from_string("3♥"))
    print(hand.getValue())
    print(hand.busted)
    hand.append(Card.from_string("T♥"))
    print(hand.getValue())
    print(hand.busted)

    for card in (hand.cards):
        print(card)

if __name__ == "__main__":
    main()
