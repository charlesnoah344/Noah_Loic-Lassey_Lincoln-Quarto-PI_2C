import pytest
import projet_quarto as ai  # Remplace "quarto_ai" par le nom réel du fichier sans le .py

@pytest.fixture
def empty_state():
    return {
        "board": [None]*16,
        "piece": None
    }

@pytest.fixture
def filled_board():
    board = [None]*16
    board[0:4] = ['BDEC', 'BDFC', 'BDEP', 'BDFP']  # ligne avec attributs en commun
    return board

def test_get_available_positions(empty_state):
    assert ai.get_available_positions(empty_state) == list(range(16))

def test_get_available_pieces(empty_state):
    assert set(ai.get_available_pieces(empty_state)) == set(ai.piece_initiales)

def test_chosen_randpos(empty_state):
    pos = ai.chosen_randpos(empty_state)
    assert pos in range(16)

def test_chosen_randpiece(empty_state):
    piece = ai.chosen_randpiece(empty_state)
    assert piece in ai.piece_initiales

def test_has_common_attribute_true():
    assert ai.has_common_attribute(['BDEC', 'BDFC', 'BDEP', 'BDFP']) is True

def test_has_common_attribute_false():
    assert ai.has_common_attribute(['BDEC', 'BLFC', 'SDEP', 'SLFP']) is False

def test_check_winner_row():
    board = ['BDEC', 'BDFC', 'BDEP', 'BDFP'] + [None]*12
    assert ai.check_winner(board) is True

def test_check_winner_none():
    board = ['BDEC', 'BLFC', 'SDEP', 'SLFP'] + [None]*12
    assert ai.check_winner(board) is False

def test_evaluate_board_score_positive(filled_board):
    assert ai.evaluate_board(filled_board) > 0

def test_evaluate_blocking_potential_penalty():
    board = [None]*16
    board[0:3] = ['BDEC', 'BDEC', 'BDEC']  # ligne presque gagnante
    assert ai.evaluate_blocking_potential(board) < 0

def test_evaluate_fonction_combined_score(filled_board):
    score = ai.evaluate_fonction(filled_board)
    assert isinstance(score, (int, float))

def test_find_best_pos_returns_valid(empty_state):
    state = empty_state.copy()
    state["piece"] = "BDEC"
    pos = ai.find_best_pos(state)
    assert pos in range(16)

def test_find_best_piece_returns_valid(empty_state):
    state = empty_state.copy()
    piece = ai.find_best_piece(state)
    assert piece in ai.piece_initiales
