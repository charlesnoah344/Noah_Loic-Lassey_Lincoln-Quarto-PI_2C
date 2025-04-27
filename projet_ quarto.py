import socket
import json
import time as time
import random
import copy
#variables
port=667
nom='Noah et Lassey'
matricules=["23397","23158"]
timeout=2.8
server_address=('localhost', 3000)
max_recv_length = 10000
piece_initiales=['BDEC','BDFC','BDEP','BDFP','BLEC','BLFC','BLEP','BLFP',
                 'SDEC','SDFC','SDEP','SDFP','SLEC','SLFC','SLEP','SLFP']

'''inscription au serveur'''

request={
"request": "subscribe",
"port": port,
"name": nom,
"matricules": matricules
}
with socket.socket() as s:
    s.connect(server_address)
    s.send(json.dumps(request).encode())#envoie de la requete d'inscription
    response = s.recv(max_recv_length).decode()
print(response)
def main():
    # print("------------------------")
    with socket.socket() as s:
        s.bind(('', port))
        s.settimeout(1)
        s.listen()
        try:
            client, address = s.accept()
            with client:
                request = client.recv(max_recv_length).decode()
                # print("request =  ",request)
                req = json.loads(request)
                message = req["request"]
                
                start_time=time.time() 
                
                if message == "ping":
                    client.send(json.dumps({'response': 'pong'}).encode())
                elif message == "play":
                    state=req["state"]
                    my_index=state['current']
                    my_piece=state['piece']
                    error_list = req["errors"]
                    print("ERRORS : ", error_list)
                    flag = False
                    if not len(error_list) == 0:
                        flag  = True
                    chosen_move = {"pos": find_best_pos(state), "piece": find_best_piece(state) }
                    client.send(json.dumps({'response': 'move', 'move': chosen_move, "message" : "appreciate" }).encode())
        except socket.timeout:
            pass
        except OSError:
            print("Server address not reachable.")

'''fonctions'''
def get_available_positions(state):
    '''cette fonction retourne la liste des positions disponibles sur la grille de jeu'''
    return [i for i, v in enumerate(state["board"]) if v is None]

def get_available_pieces(state):
    '''cette fonction retourne la liste des pièces restantes de la partie'''
    used = set(p for p in state["board"] if p is not None)
    if state["piece"]:
        used.add(state["piece"])
    return list(set(piece_initiales)-used)#retourne les pièces restantes

def chosen_randpos(state):
    '''cette fonction détermine la position de la pièce'''
    position=get_available_positions(state)
    pos=random.choice(position)
    return pos

def chosen_randpiece(state):
    '''cette fonction détermine la pièce à donner à l' adversaire'''
    pieces=get_available_pieces(state)
    piece=random.choice(pieces)
    return piece

def has_common_attribute(pieces):
    """Cette fonction évalue si les pièces d'une liste ont un attribut commun"""
    if not pieces or None in pieces:
        return False
    for i in range(4):  # Check each attribute
        if len(set(p[i] for p in pieces)) == 1:
            return True
    return False
def check_winner(board):
        """évalue l'existence d'une ligne gagnante et retourne un booléen"""
        # Convert linear board to 4x4 grid
        grid = [board[i*4:(i+1)*4] for i in range(4)]
        
        # Check rows, columns, and diagonals
        for i in range(4):
            # Rows
            row = grid[i]
            if None not in row and has_common_attribute(row):
                return True
            # Columns
            column = [grid[j][i] for j in range(4)]
            if None not in column and has_common_attribute(column):
                return True
        
        # Diagonals
        diag1 = [grid[i][i] for i in range(4)]
        diag2 = [grid[i][3-i] for i in range(4)]
        if None not in diag1 and has_common_attribute(diag1):
            return True
        if None not in diag2 and has_common_attribute(diag2):
            return True
        
        
        return False

def evaluate_board(board):
        """Cette fonction est une héristique permetttant à l'IA de priviligier le palcement de pièces ayant un attribut commun"""

        score = 0 #représente le nombre de pièce avec un attribut commmun alignés
        grid = [board[i*4:(i+1)*4] for i in range(4)]
        
        for i in range(4):
            # Rows
            row = grid[i]
            if None in row:
                # Count how many pieces share attributes in incomplete rows
                for attr_idx in range(4):
                    attrs = [p[attr_idx] for p in row if p is not None]
                    if len(set(attrs)) == 1:
                        score += len(attrs)
            # Columns
            column = [grid[j][i] for j in range(4)]
            if None in column:
                for attr_idx in range(4):
                    attrs = [p[attr_idx] for p in column if p is not None]
                    if len(set(attrs)) == 1:
                        score += len(attrs)
        
        # Diagonals
        diag1 = [grid[i][i] for i in range(4)]
        diag2 = [grid[i][3-i] for i in range(4)]
        for diag in [diag1, diag2]:
            if None in diag:
                for attr_idx in range(4):
                    attrs = [p[attr_idx] for p in diag if p is not None]
                    if len(set(attrs)) == 1:
                        score += len(attrs)
        
        return score
def find_best_pos(state):
        """Trouve la position optimale avec alpha-beta pruning."""
        current_piece=state['piece']
        board=state["board"]
            # Place the piece on the board
        best_score = -float('inf')
        best_pos = None
        available_positions = get_available_positions(state)
        available_pieces = get_available_pieces(state)
        start_time = time.time()

            
        # Vérifier d'abord les positions gagnantes immédiates
        for pos in available_positions:
            new_board = board.copy()
            new_board[pos] = current_piece
            if check_winner(new_board):
                return pos
          # Si pas de victoire immédiate, utiliser minimax
        for pos in available_positions:
            # Si on approche du timeout, retourner la meilleure position trouvée jusqu'à présent
            if time.time() - start_time > timeout * 0.7:
                break
                
            new_board = board.copy()
            new_board[pos] = current_piece
            
            score = minimax(
                state,
                new_board, 
                available_pieces,  # Utiliser la liste déjà calculée
                None, 
                depth=3,  # Réduire la profondeur pour être sûr de terminer à temps
                is_maximizing=True,  # On veut maximiser notre score
                alpha=-float('inf'), 
                beta=float('inf'),
                start_time=start_time  # Utiliser le même chronomètre
            )
            
            if score > best_score:
                best_score = score
                best_pos = pos
        
        return best_pos if best_pos is not None else chosen_randpos(state)

def find_best_piece(state):
    """Trouve la pièce optimale pour l'adversaire avec alpha-beta pruning."""
    board=state["board"]
    best_score = -float('inf')
    best_piece = None
    available_pieces = get_available_pieces(state)
    start_time = time.time()  # Un seul chronomètre pour toute la fonction

            
    for piece in available_pieces:
                # Si on approche du timeout, retourner la meilleure pièce trouvée jusqu'à présent
                if time.time() - start_time > timeout * 0.7:
                    break
                score = minimax(state,
                    board.copy(),
                    [p for p in get_available_pieces(state) if p != piece],
                    piece,
                    depth=3,
                    is_maximizing=True,
                    alpha=-float('inf'),
                    beta=float('inf'),
                    start_time=start_time
                )
                
                if score > best_score:
                    best_score = score
                    best_piece = piece
            
    return best_piece if best_piece is not None else chosen_randpiece(state)


def minimax( state, board, remaining_pieces, current_piece, 
                depth, is_maximizing, alpha, beta, start_time):
        """Minimax algorithm with alpha-beta pruning."""



        if time.time() - start_time > timeout * 0.8:
            return 0
        
        # Terminal conditions
        if check_winner(board):
            return 100 if not is_maximizing else -100
        if depth == 0 or not remaining_pieces:
            return evaluate_board(board)
        
        if current_piece is not None:
            # Place the piece
            if is_maximizing:
                max_score = -float('inf')
                for pos in range(16):
                    if board[pos] is None:
                        new_board = board.copy()
                        new_board[pos] = current_piece
                        score = minimax(state, new_board, remaining_pieces, None, depth-1, False, alpha, beta, start_time)
                        max_score = max(max_score, score)
                        alpha = max(alpha, score)
                        if beta <= alpha:
                            break
                return max_score
            else:
                min_score = float('inf')
                for pos in range(16):
                    if board[pos] is None:
                        new_board = board.copy()
                        new_board[pos] = current_piece
                        score = minimax(state, new_board, remaining_pieces, None, depth-1, True, alpha, beta, start_time)
                        min_score = min(min_score, score)
                        beta = min(beta, score)
                        if beta <= alpha:
                            break
                return min_score
        else:
            # Choose a piece
            if is_maximizing:
                max_score = -float('inf')
                for piece in remaining_pieces:
                    new_remaining = [p for p in remaining_pieces if p != piece]
                    score = minimax(state, board.copy(), new_remaining, piece, depth-1, False, alpha, beta, start_time)
                    max_score = max(max_score, score)
                    alpha = max(alpha, score)
                    if beta <= alpha:
                        break
                return max_score
            else:
                min_score = float('inf')
                for piece in remaining_pieces:
                    new_remaining = [p for p in remaining_pieces if p != piece]
                    score = minimax(state, board.copy(), new_remaining, piece, depth-1, True, alpha, beta, start_time)
                    min_score = min(min_score, score)
                    beta = min(beta, score)
                    if beta <= alpha:
                        break
                return min_score


'''programme principal'''

while __name__ == '__main__':
    main()



