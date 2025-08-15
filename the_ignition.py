import os
import time
from deck import Deck, Card, Suits, Ranks
from typing import List
import sys

print("hi")



NUM_HANDS = 5
STARTING_WALLET = 100

print("blackjack simulator")
print(f"Let's play some blackjack! Here, start with ${STARTING_WALLET}.")

class BlackjackGame:

    def __init__(self):
        self.hands: List[List[Card]] = [[] for _ in range(NUM_HANDS)]
        self.wallets: List[int] = [STARTING_WALLET for _ in range(NUM_HANDS)]
        self.dealer_hand: List[Card] = []
        self.deck = Deck()
        self.deck.shuffle()

        self.isDrawn = False

    def playHand(self):
        print("Dealing", end="")

        self.dealer_hand.append(self.deck.draw())
        for i in range(NUM_HANDS):
            print(".", end="")
            self.hands[i].append(self.deck.draw())
        print("")
        self.dealer_hand.append(self.deck.draw())
        self.dealer_hand.append(self.deck.draw(flipped=True))

        self.drawGame()

        for _ in range(230):
            self.dealer_hand.append(self.deck.draw())

            self.drawGame()

            time.sleep(0.05)


    def drawGame(self):

        terminal_width = 120
        terminal_height = 7

        # def clear_last_n_lines(n=3):
        #     for _ in range(n):
        #         # Move cursor up one line
        #         sys.stdout.write('\x1b[1A')
        #         # Clear the line
        #         sys.stdout.write('\x1b[2K')
        #     sys.stdout.flush()

        # if(self.isDrawn):
        #     clear_last_n_lines(terminal_height)
        # else:
        #     self.isDrawn = True

        def clear_screen():
            # Clears the entire terminal screen
            os.system('cls' if os.name == 'nt' else 'clear')

        clear_screen()


        # fill
        self.symbols = [" " for _ in range(terminal_width * terminal_height)]

        center_x = terminal_width // 2
        for index, card in enumerate(self.dealer_hand):
            x_pos = center_x - 3 + (index * 3)
            reserve = card.ascii_art_coords()
            for item in reserve:
                x = item['x'] + x_pos - 2
                y = item['y']
                if 0 <= x < terminal_width and 0 <= y < terminal_height:
                    self.symbols[x + (y * terminal_width)] = item['symbol']

        # draw
        for y in range(terminal_height):
            for x in range(terminal_width):
                print(self.symbols[x+(y*terminal_width)], end="")
            print("")


        # print("D: ".ljust(8), end="")
        # for card in self.dealer_hand:
        #     print(card, end=" ")
        # print("\nHands:")
        # for hand in self.hands:
        #     print("H: ".ljust(8), end="")
        #     for card in hand:
        #         print(card, end=" ")






game = BlackjackGame()


game.playHand()

