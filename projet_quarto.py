import socket
import json
import time
import random
from functools import lru_cache

# Configuration
PORT = 677
NOM = 'Lamine_Yamal_ssj3'
MATRICULES = ["23397", "23158"]
TIMEOUT = 3.0
SERVER_ADDRESS = ('172.17.10.133', 3000)
MAX_RECV_LENGTH = 10000


# Inscription au serveur
def s_inscrire():
    request = {
        "request": "subscribe",
        "port": PORT,
        "name": NOM,
        "matricules": MATRICULES
    }
    with socket.socket() as s:
        s.connect(SERVER_ADDRESS)
        s.send(json.dumps(request).encode())
        response = s.recv(MAX_RECV_LENGTH).decode()
    print("Réponse du serveur:", response)

# Fonctions utilitaires améliorées
def get_available_positions(board):
    """Retourne les positions disponibles triées par importance (centre > coins > bords)"""
    positions = [i for i, p in enumerate(board) if p is None]
    position_values = [3 if i in [5, 6, 9, 10] else 2 if i in [0, 3, 12, 15] else 1 for i in range(16)]
    positions.sort(key=lambda x: -position_values[x])#on trie selon la valeur négative (pour trier du plus grand au plus petit).
    return positions

def get_available_pieces(state):
    used = set(frozenset(p) for p in state["board"] if p is not None)
    if state["piece"]:
        used.add(frozenset(state["piece"]))

    all_pieces = set()
    for size in ["B", "S"]:
        for color in ["D", "L"]:
            for weight in ["E", "F"]:
                for shape in ["C", "P"]:
                    all_pieces.add(frozenset(size + color + weight + shape))
    list_res=[]
    for elem in list(all_pieces-used):
        mot=''.join(elem)
        list_res.append(mot)
    return  list_res

def piece_danger_score(piece, board):
    """Évalue à quel point une pièce est dangereuse pour l'adversaire"""
    score = 0
    for pos in get_available_positions(board):
        new_board = board.copy()
        new_board[pos] = piece
        if check_winner(new_board):
            score += 100  # Pièce qui peut faire gagner immédiatement
    return score

# Fonctions d'évaluation améliorées
def has_common_attribute(pieces):
    """Vérifie si les pièces ont un attribut commun"""
    if not pieces or None in pieces:
        return False
    for i in range(4):  # Vérifie chaque attribut
        if len(set(p[i] for p in pieces)) == 1:
            return True
    return False

def check_winner(board):
    """Vérifie s'il y a un gagnant sur le plateau"""
    # Convertir en grille 4x4
    grid = [board[i*4:(i+1)*4] for i in range(4)]
    
    # Vérifier lignes et colonnes
    for i in range(4):
        row = grid[i]
        if None not in row and has_common_attribute(row):
            return True
        column = [grid[j][i] for j in range(4)]
        if None not in column and has_common_attribute(column):
            return True
    
    # Vérifier diagonales
    diag1 = [grid[i][i] for i in range(4)]
    diag2 = [grid[i][3-i] for i in range(4)]
    if (None not in diag1 and has_common_attribute(diag1)) or \
       (None not in diag2 and has_common_attribute(diag2)):
        return True
    
    return False

def evaluate_board(board):
    """Heuristique sophistiquée pour évaluer le plateau"""
    score = 0
    lines = []
    
    # Toutes les lignes possibles
    for i in range(4):
        lines.append([board[i*4 + j] for j in range(4)])  # Lignes
        lines.append([board[j*4 + i] for j in range(4)])  # Colonnes
    lines.append([board[i*4 + i] for i in range(4)])     # Diagonale 1
    lines.append([board[i*4 + (3-i)] for i in range(4)]) # Diagonale 2
    
    for line in lines:
        if None in line:
            # Évaluer les lignes incomplètes
            filled = [p for p in line if p is not None]
            count = len(filled)
            
            for attr in range(4):
                unique_attrs = set(p[attr] for p in filled)
                if len(unique_attrs) == 1:
                    score += 10 * count  # Bonus pour attributs communs
                elif count == 3 and len(unique_attrs) == 2:
                    score -= 20  # Pénalité pour situation dangereuse
        else:
            # Ligne complète
            for attr in range(4):
                if len(set(p[attr] for p in line)) == 1:
                    return float('inf')  # Victoire
    
    # Bonus pour le centre et les coins
    center_positions = [5, 6, 9, 10]
    for pos in center_positions:
        if board[pos] is not None:
            score += 5
    
    return score

# Algorithme Minimax optimisé
@lru_cache(maxsize=None)
def minimax_cached(board_tuple, pieces_tuple, current_piece, depth, is_maximizing, alpha, beta):
    """Version avec mémoization de l'algorithme Minimax"""
    board = list(board_tuple)
    remaining_pieces = list(pieces_tuple) if pieces_tuple else []
    
    # Conditions terminales
    if check_winner(board):
        return float('inf') if not is_maximizing else -float('inf')
    if depth == 0 or not remaining_pieces:
        return evaluate_board(board)
    
    if current_piece is not None:
        # Placer la pièce
        if is_maximizing:
            max_score = -float('inf')
            for pos in get_available_positions(board):
                new_board = board.copy()
                new_board[pos] = current_piece
                score = minimax_cached(
                    tuple(new_board), tuple(remaining_pieces), None,
                    depth-1, False, alpha, beta
                )
                max_score = max(max_score, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return max_score
        else:
            min_score = float('inf')
            for pos in get_available_positions(board):
                new_board = board.copy()
                new_board[pos] = current_piece
                score = minimax_cached(
                    tuple(new_board), tuple(remaining_pieces), None,
                    depth-1, True, alpha, beta
                )
                min_score = min(min_score, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return min_score
    else:
        # Choisir une pièce
        pieces = sorted(remaining_pieces, key=lambda p: -piece_danger_score(p, board))
        
        if is_maximizing:
            max_score = -float('inf')
            for piece in pieces:
                new_remaining = [p for p in remaining_pieces if p != piece]
                score = minimax_cached(
                    tuple(board), tuple(new_remaining), piece,
                    depth-1, False, alpha, beta
                )
                max_score = max(max_score, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return max_score
        else:
            min_score = float('inf')
            for piece in pieces:
                new_remaining = [p for p in remaining_pieces if p != piece]
                score = minimax_cached(
                    tuple(board), tuple(new_remaining), piece,
                    depth-1, True, alpha, beta
                )
                min_score = min(min_score, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return min_score

def adaptive_depth(state, time_remaining):
    """Détermine la profondeur de recherche en fonction du temps et de l'état du jeu"""
    remaining_pieces = len(get_available_pieces(state))
    
    if time_remaining > 3.0:
        if remaining_pieces > 12:
            return 3
        elif remaining_pieces > 8:
            return 4
        else:
            return 5
    elif time_remaining > 1.5:
        return 3
    else:
        return 2

# Fonctions principales améliorées
def find_best_pos(state, start_time):
    """Trouve la meilleure position pour placer la pièce actuelle"""
    board = state["board"]
    current_piece = state["piece"]
    remaining_pieces = get_available_pieces(state)
    time_remaining = TIMEOUT - (time.time() - start_time)
    
    # Vérifier les coups gagnants immédiats
    for pos in get_available_positions(board):
        new_board = board.copy()
        new_board[pos] = current_piece
        if check_winner(new_board):
            return pos
    
    # Vérifier les coups perdants à bloquer
    for piece in remaining_pieces:
        for pos in get_available_positions(board):
            new_board = board.copy()
            new_board[pos] = piece
            if check_winner(new_board):
                # Éviter de donner cette position à l'adversaire
                pass
    
    # Recherche Minimax avec profondeur adaptative
    depth = adaptive_depth(state, time_remaining)
    best_score = -float('inf')
    best_pos = None
    alpha = -float('inf')
    beta = float('inf')
    
    for pos in get_available_positions(board):
        if time.time() - start_time > TIMEOUT * 0.8:
            break
            
        new_board = board.copy()
        new_board[pos] = current_piece
        score = minimax_cached(
            tuple(new_board), tuple(remaining_pieces), None,
            depth-1, False, alpha, beta
        )
        
        if score > best_score:
            best_score = score
            best_pos = pos
            alpha = max(alpha, score)
    
    return best_pos if best_pos is not None else get_available_positions(board)[0]

def find_best_piece(state, start_time):
    """Trouve la meilleure pièce à donner à l'adversaire"""
    board = state["board"]
    remaining_pieces = get_available_pieces(state)
    time_remaining = TIMEOUT - (time.time() - start_time)
    depth = adaptive_depth(state, time_remaining)
    
    best_score = -float('inf')
    best_piece = None
    alpha = -float('inf')
    beta = float('inf')
    
    # Trier les pièces par dangerosité
    pieces = sorted(remaining_pieces, key=lambda p: piece_danger_score(p, board))
    
    for piece in pieces:
        if time.time() - start_time > TIMEOUT * 0.8:
            break
            
        new_remaining = [p for p in remaining_pieces if p != piece]
        score = minimax_cached(
            tuple(board), tuple(new_remaining), piece,
            depth-1, True, alpha, beta
        )
        
        if score > best_score:
            best_score = score
            best_piece = piece
            alpha = max(alpha, score)
    
    return best_piece if best_piece is not None else random.choice(remaining_pieces)

# Boucle principale
def main():
    with socket.socket() as s:
        s.bind(('', PORT))
        s.settimeout(1)
        s.listen()
        try:
            client, address = s.accept()
            with client:
                request = client.recv(MAX_RECV_LENGTH).decode()
                req = json.loads(request)
                message = req["request"]
                
                start_time = time.time()
                
                if message == "ping":
                    client.send(json.dumps({'response': 'pong'}).encode())

                elif message == "play":
                    state = req["state"]
                    chosen_move = {
                        "pos": find_best_pos(state, start_time),
                        "piece": find_best_piece(state, start_time)
                    }
                    client.send(json.dumps({
                        'response': 'move',
                        'move': chosen_move,
                        'message': 'Stay humble ehh'
                    }).encode())
                    error_list = req["errors"]
                    print("ERRORS : ", error_list)
                    print(chosen_move)
        except socket.timeout:
            pass
        except Exception as e:
            print(f"Erreur: {e}")

# Point d'entrée
if __name__ == '__main__':
    s_inscrire()
    while True:
        main()