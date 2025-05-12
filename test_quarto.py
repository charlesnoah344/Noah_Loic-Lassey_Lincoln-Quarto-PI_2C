import pytest
import copy
import random
import socket
import json
from unittest.mock import MagicMock, patch
import sys
import os

# Add the parent directory to path so we can import the module to test
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import projet_quarto

# Test fixtures
@pytest.fixture
def empty_board():
    return [None] * 16

@pytest.fixture
def sample_board():
    board = [None] * 16
    board[0] = "BDEC"  # Big, Dark, Empty, Cubic
    board[5] = "BLEP"  # Big, Light, Empty, Pyramidal
    board[10] = "SDFP" # Small, Dark, Full, Pyramidal
    board[15] = "SLFC" # Small, Light, Full, Cubic
    return board

@pytest.fixture
def winning_board():
    board = [None] * 16
    # Create a winning row with all Small pieces
    board[0] = "SDEC"
    board[1] = "SLEP"
    board[2] = "SDFC"
    board[3] = "SLFP"
    return board

@pytest.fixture
def nearly_winning_board():
    board = [None] * 16
    # Create a board with 3 small pieces in a row
    board[0] = "SDEC"
    board[1] = "SLEP"
    board[2] = "SDFC"
    # Position 3 is empty but could complete a winning row
    return board

@pytest.fixture
def sample_state(sample_board):
    return {
        "board": sample_board,
        "piece": "BDEP",
        "errors": []
    }

@pytest.fixture
def empty_state(empty_board):
    return {
        "board": empty_board,
        "piece": "BDEP",
        "errors": []
    }

# Test utility functions
def test_get_available_positions(empty_board, sample_board):
    # Test with empty board
    positions = projet_quarto.get_available_positions(empty_board)
    assert len(positions) == 16
    # Center positions should come first (higher priority)
    assert all(pos in [5, 6, 9, 10] for pos in positions[:4])
    
    # Test with partially filled board
    positions = projet_quarto.get_available_positions(sample_board)
    assert len(positions) == 12
    assert 0 not in positions
    assert 5 not in positions
    assert 10 not in positions
    assert 15 not in positions

def test_get_available_pieces():
    # Test with empty board and no selected piece
    state = {"board": [None] * 16, "piece": None}
    pieces = projet_quarto.get_available_pieces(state)
    assert len(pieces) == 16  # All 16 pieces should be available
    
    # Test with some pieces on board and selected piece
    state = {
        "board": [None] * 16,
        "piece": "BDEC"
    }
    state["board"][0] = "BLEP"
    state["board"][1] = "SDFP"
    
    pieces = projet_quarto.get_available_pieces(state)
    assert len(pieces) == 13  # 16 - 3 = 13 pieces available
    assert "BDEC" not in pieces
    assert "BLEP" not in pieces
    assert "SDFP" not in pieces

def test_piece_danger_score(empty_board, nearly_winning_board):
    # Test with an empty board (no immediate danger)
    score = projet_quarto.piece_danger_score("SDEP", empty_board)
    assert score == 0
    
    # Test with a nearly winning board
    # "SLFP" would complete a row of small pieces
    score = projet_quarto.piece_danger_score("SLFP", nearly_winning_board)
    assert score > 0

def test_has_common_attribute():
    # Test with pieces sharing an attribute (all small)
    pieces = ["SDEC", "SLEP", "SDFC", "SLFP"]
    assert projet_quarto.has_common_attribute(pieces) == True
    
    # Test with pieces not sharing any attribute
    pieces = ["BDEC", "SLEP", "SDFC", "BLFP"]
    assert projet_quarto.has_common_attribute(pieces) == False
    
    # Test with None in pieces
    pieces = ["BDEC", None, "SDFC", "BLFP"]
    assert projet_quarto.has_common_attribute(pieces) == False
    
    # Test with empty list
    assert projet_quarto.has_common_attribute([]) == False

def test_check_winner(empty_board, winning_board, sample_board):
    # Test with empty board (no winner)
    assert projet_quarto.check_winner(empty_board) == False
    
    # Test with winning board (row with all small pieces)
    assert projet_quarto.check_winner(winning_board) == True
    
    # Test with non-winning board
    assert projet_quarto.check_winner(sample_board) == False
    
    # Test winning column
    column_win = copy.deepcopy(empty_board)
    column_win[0] = "BDEC"
    column_win[4] = "BLEC"
    column_win[8] = "SDEC"
    column_win[12] = "SLEC"
    assert projet_quarto.check_winner(column_win) == True  # All cubic
    
    # Test winning diagonal
    diag_win = copy.deepcopy(empty_board)
    diag_win[0] = "BDEP"
    diag_win[5] = "BLEP"
    diag_win[10] = "SDEP"
    diag_win[15] = "SLEP"
    assert projet_quarto.check_winner(diag_win) == True  # All pyramidal

def test_evaluate_board(empty_board, sample_board, winning_board):
    # Test empty board evaluation
    score_empty = projet_quarto.evaluate_board(empty_board)
    assert isinstance(score_empty, (int, float))
    
    # Test sample board evaluation
    score_sample = projet_quarto.evaluate_board(sample_board)
    assert isinstance(score_sample, (int, float))
    
    # Test winning board evaluation
    score_winning = projet_quarto.evaluate_board(winning_board)
    assert score_winning == float('inf')  # Should return infinity for winning board

def test_adaptive_depth():
    # Test with lots of time and many pieces
    state = {"board": [None] * 16, "piece": "BDEP"}
    depth = projet_quarto.adaptive_depth(state, 5.0)
    assert depth >= 3
    
    # Test with little time
    depth = projet_quarto.adaptive_depth(state, 1.0)
    assert depth >= 2
    
    # Test with few pieces remaining
    state["board"] = ["BDEC"] * 8 + [None] * 8
    depth = projet_quarto.adaptive_depth(state, 5.0)
    assert depth >= 3

def test_minimax_cached():
    # Basic test with simple board
    board = [None] * 16
    board[0] = "BDEC"
    pieces = ["SLEP", "SDFC"]
    
    # Test maximizing player
    score = projet_quarto.minimax_cached(
        tuple(board), tuple(pieces), "BDEP", 
        2, True, float('-inf'), float('inf')
    )
    assert isinstance(score, (int, float))
    
    # Test minimizing player
    score = projet_quarto.minimax_cached(
        tuple(board), tuple(pieces), "BDEP", 
        2, False, float('-inf'), float('inf')
    )
    assert isinstance(score, (int, float))
    
    # Test with None as current piece (piece selection phase)
    score = projet_quarto.minimax_cached(
        tuple(board), tuple(pieces), None, 
        2, True, float('-inf'), float('inf')
    )
    assert isinstance(score, (int, float))

def test_find_best_piece(sample_state, empty_state):
    # Test finding best piece on sample board
    start_time = 0
    
    with patch('time.time', side_effect=[0, 0.5, 1.0, 1.5]):
        # Mock get_available_pieces to return a smaller set for faster testing
        with patch('projet_quarto.get_available_pieces', return_value=["SLFC", "SDEP", "BLFC"]):
            piece = projet_quarto.find_best_piece(sample_state, start_time)
            assert piece in ["SLFC", "SDEP", "BLFC"]
    
    # Test with time constraint
    with patch('time.time', side_effect=[0, 3.0]):
        with patch('projet_quarto.get_available_pieces', return_value=["SLFC", "SDEP"]):
            piece = projet_quarto.find_best_piece(empty_state, start_time)
            assert piece in ["SLFC", "SDEP"]

# Network/integration tests
def test_s_inscrire():
    with patch('socket.socket') as mock_socket:
        mock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_instance
        mock_instance.recv.return_value = b'{"status": "ok"}'
        
        projet_quarto.s_inscrire()
        
        # Check that connect was called with the right arguments
        mock_instance.connect.assert_called_with(projet_quarto.SERVER_ADDRESS)
        # Check that the right request was sent
        sent_data = mock_instance.send.call_args[0][0].decode()
        sent_json = json.loads(sent_data)
        assert sent_json["request"] == "subscribe"
        assert sent_json["port"] == projet_quarto.PORT
        assert sent_json["name"] == projet_quarto.NOM
        assert sent_json["matricules"] == projet_quarto.MATRICULES

def test_main_ping():
    with patch('socket.socket') as mock_socket:
        # Setup mock socket
        mock_server = MagicMock()
        mock_client = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_server
        mock_server.accept.return_value = (mock_client, ('127.0.0.1', 1234))
        mock_client.__enter__.return_value = mock_client
        mock_client.recv.return_value = json.dumps({
            "request": "ping"
        }).encode()
        
        projet_quarto.main()
        
        # Check response
        sent_data = mock_client.send.call_args[0][0].decode()
        sent_json = json.loads(sent_data)
        assert sent_json["response"] == "pong"

def test_main_play():
    with patch('socket.socket') as mock_socket:
        # Setup mock socket
        mock_server = MagicMock()
        mock_client = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_server
        mock_server.accept.return_value = (mock_client, ('127.0.0.1', 1234))
        mock_client.__enter__.return_value = mock_client
        
        # Create a game state
        state = {
            "board": [None] * 16,
            "piece": "BDEP",
            "errors": []
        }
        mock_client.recv.return_value = json.dumps({
            "request": "play",
            "state": state,
            "errors": []
        }).encode()
        
        # Mock time to avoid actual waiting
        with patch('time.time', return_value=0):
            # Mock decision functions to speed up test
            with patch('projet_quarto.find_best_pos', return_value=0):
                with patch('projet_quarto.find_best_piece', return_value="SLFC"):
                    projet_quarto.main()
        
        # Check response
        sent_data = mock_client.send.call_args[0][0].decode()
        sent_json = json.loads(sent_data)
        assert sent_json["response"] == "move"
        assert "move" in sent_json
        assert sent_json["move"]["pos"] == 0
        assert sent_json["move"]["piece"] == "SLFC"

def test_main_exception_handling():
    # Test socket timeout
    with patch('socket.socket') as mock_socket:
        mock_server = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_server
        mock_server.accept.side_effect = socket.timeout
        
        # Should not raise exception
        projet_quarto.main()
    
    # Test generic exception
    with patch('socket.socket') as mock_socket:
        mock_server = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_server
        mock_server.accept.side_effect = Exception("Test exception")
        
        # Should not raise exception, but print error
        with patch('builtins.print') as mock_print:
            projet_quarto.main()
            mock_print.assert_called()

# Run the tests with coverage:
# python -m pytest test_projet_quarto.py -v --cov=projet_quarto --cov-report term-missing
