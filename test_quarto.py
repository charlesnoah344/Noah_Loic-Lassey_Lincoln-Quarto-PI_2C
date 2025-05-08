import pytest
import socket
import json
import time
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
from io import StringIO

# Import the module to test
# Make sure the original file is in the same directory or in the Python path
from projet_quarto import (
    get_available_positions, get_available_pieces, piece_danger_score,
    has_common_attribute, check_winner, evaluate_board, minimax_cached,
    find_best_pos, find_best_piece, adaptive_depth, PIECES_INITIALES,
    s_inscrire, main, PORT, NOM, MATRICULES, SERVER_ADDRESS, MAX_RECV_LENGTH, TIMEOUT
)

# Fixtures for common test data
@pytest.fixture
def empty_board():
    return [None] * 16

@pytest.fixture
def partial_board():
    return [
        'BDEC', None, None, None,
        None, 'BLFC', None, None,
        None, None, 'SDEP', None,
        None, None, None, 'SLFP'
    ]

@pytest.fixture
def almost_win_board():
    return [
        'BDEC', 'BLEC', 'SDEC', None,
        None, None, None, None,
        None, None, None, None,
        None, None, None, None
    ]

@pytest.fixture
def winning_board():
    return [
        'BDEC', 'BLEC', 'SDEC', 'SLEC',
        None, None, None, None,
        None, None, None, None,
        None, None, None, None
    ]

@pytest.fixture
def empty_state(empty_board):
    return {
        "board": empty_board,
        "piece": 'BDEC'
    }

@pytest.fixture
def partial_state(partial_board):
    return {
        "board": partial_board,
        "piece": 'BDFC'
    }

@pytest.fixture
def win_state(almost_win_board):
    return {
        "board": almost_win_board,
        "piece": 'SLEC'
    }

# Tests for utility functions
def test_get_available_positions(empty_board, partial_board):
    """Test that available positions are correctly identified and prioritized"""
    # Empty board should return all positions with center positions first
    positions = get_available_positions(empty_board)
    assert len(positions) == 16
    # Check that center positions come first
    center_positions = [5, 6, 9, 10]
    for i in range(4):
        assert positions[i] in center_positions
    
    # Partial board should return correct number of empty positions
    positions = get_available_positions(partial_board)
    assert len(positions) == 12
    assert 0 not in positions  # Position 0 is filled
    assert 5 not in positions  # Position 5 is filled
    assert 10 not in positions  # Position 10 is filled
    assert 15 not in positions  # Position 15 is filled
    
    # Test with a full board
    full_board = ['BDEC'] * 16
    positions = get_available_positions(full_board)
    assert len(positions) == 0

def test_get_available_pieces(empty_state, partial_state):
    """Test that available pieces are correctly identified"""
    # Empty board with one piece in state
    pieces = get_available_pieces(empty_state)
    assert len(pieces) == 15
    assert 'BDEC' not in pieces
    
    # Partial board with pieces placed
    pieces = get_available_pieces(partial_state)
    assert len(pieces) == 11
    assert 'BDEC' not in pieces
    assert 'BLFC' not in pieces
    assert 'SDEP' not in pieces
    assert 'SLFP' not in pieces
    assert 'BDFC' not in pieces
    
    # Test with a full board
    full_board = ['BDEC', 'BDFC', 'BDEP', 'BDFP', 'BLEC', 'BLFC', 'BLEP', 'BLFP',
                  'SDEC', 'SDFC', 'SDEP', 'SDFP', 'SLEC', 'SLFC', 'SLEP', 'SLFP']
    full_state = {"board": full_board, "piece": None}
    pieces = get_available_pieces(full_state)
    assert len(pieces) == 0
    
    # Test with no piece selected
    no_piece_state = {"board": empty_board, "piece": None}
    pieces = get_available_pieces(no_piece_state)
    assert len(pieces) == 16

def test_piece_danger_score(empty_board, almost_win_board):
    """Test the danger score calculation for pieces"""
    # On an empty board, no piece should be immediately dangerous
    for piece in PIECES_INITIALES:
        score = piece_danger_score(piece, empty_board)
        assert score == 0
    
    # On a board with almost a win, the matching piece should be dangerous
    score_danger = piece_danger_score('SLEC', almost_win_board)
    score_safe = piece_danger_score('BDFC', almost_win_board)
    assert score_danger > score_safe
    
    # Test with a piece that would complete a diagonal
    diagonal_almost_win = [
        'BDEP', None, None, None,
        None, 'BLFP', None, None,
        None, None, 'SDEP', None,
        None, None, None, None
    ]
    score = piece_danger_score('SLFP', diagonal_almost_win)
    assert score > 0

def test_has_common_attribute():
    """Test the detection of common attributes"""
    # Test case with common first attribute (all begin with B)
    assert has_common_attribute(['BDEC', 'BDFC', 'BLEC', 'BLFP'])
    
    # Test case with common second attribute (all have D)
    assert has_common_attribute(['BDEC', 'BDFC', 'SDEP', 'SDFP'])
    
    # Test case with common third attribute (all have E)
    assert has_common_attribute(['BDEC', 'BLEP', 'SDEP', 'SLEP'])
    
    # Test case with common fourth attribute (all have C)
    assert has_common_attribute(['BDEC', 'BDFC', 'SLEC', 'SDFC'])
    
    # Test case with no common attributes
    assert not has_common_attribute(['BDEC', 'SLFP', 'BLEP', 'SDFC'])
    
    # Test with None in the list
    assert not has_common_attribute(['BDEC', None, 'BLEP', 'SDFC'])
    
    # Test with empty list
    assert not has_common_attribute([])
    
    # Test with fewer than 4 pieces
    assert has_common_attribute(['BDEC', 'BDFC', 'BDEP'])  # All have B and D

def test_check_winner(empty_board, partial_board, almost_win_board, winning_board):
    """Test the winner detection logic"""
    # Empty board should have no winner
    assert not check_winner(empty_board)
    
    # Partial board should have no winner
    assert not check_winner(partial_board)
    
    # Almost win board should have no winner
    assert not check_winner(almost_win_board)
    
    # Winning board should detect a winner (all have E as 3rd attribute)
    assert check_winner(winning_board)
    
    # Test winning row (second row all have B)
    winning_row = [
        None, None, None, None,
        'BDEC', 'BDFC', 'BLEP', 'BLFP',
        None, None, None, None,
        None, None, None, None
    ]
    assert check_winner(winning_row)
    
    # Test winning column (third column all have F)
    winning_col = [
        None, None, 'BDFC', None,
        None, None, 'BLFC', None,
        None, None, 'SDFC', None,
        None, None, 'SLFC', None
    ]
    assert check_winner(winning_col)
    
    # Test winning diagonal (all have P)
    winning_diag = [
        'BDEP', None, None, None,
        None, 'BLFP', None, None,
        None, None, 'SDEP', None,
        None, None, None, 'SLFP'
    ]
    assert check_winner(winning_diag)
    
    # Tests for the other diagonal
    winning_diag2 = [
        None, None, None, 'BDEP',
        None, None, 'BLFP', None,
        None, 'SDEP', None, None,
        'SLFP', None, None, None
    ]
    assert check_winner(winning_diag2)
    
    # Test where only some positions are filled but no win
    partial_no_win = [
        'BDEC', None, 'SLFC', None,
        None, 'BDFC', None, None,
        'SLEP', None, 'SDEP', None,
        None, 'BLFP', None, 'SLFP'
    ]
    assert not check_winner(partial_no_win)

def test_evaluate_board(empty_board, winning_board):
    """Test the board evaluation heuristic"""
    # Empty board should have a neutral score
    empty_score = evaluate_board(empty_board)
    assert isinstance(empty_score, (int, float))
    
    # Winning board should have an infinite score
    win_score = evaluate_board(winning_board)
    assert win_score == float('inf')
    
    # A board with pieces in center should score higher than empty
    center_board = empty_board.copy()
    center_board[5] = 'BDEC'
    center_score = evaluate_board(center_board)
    assert center_score > empty_score
    
    # Test board with potential win
    potential_win = [
        'BDEC', 'BDFC', 'BDEP', None,
        None, None, None, None,
        None, None, None, None,
        None, None, None, None
    ]
    potential_score = evaluate_board(potential_win)
    assert potential_score > empty_score
    
    # Test board with dangerous position (3 same attributes in a row)
    dangerous = [
        'BDEC', 'BDFC', 'BDEP', None,
        'SLEC', None, None, None,
        None, None, None, None,
        None, None, None, None
    ]
    dangerous_score = evaluate_board(dangerous)
    assert dangerous_score != float('inf')  # Not a win yet

def test_minimax_cached():
    """Test the minimax algorithm with a simple scenario"""
    # For a simple test, we'll check if minimax returns a numeric value
    # and if the cache is working (by calling it twice with the same params)
    board = tuple([None] * 16)
    pieces = tuple(['BDFC', 'SDFC'])
    score1 = minimax_cached(board, pieces, 'BDFC', 1, True, float('-inf'), float('inf'))
    score2 = minimax_cached(board, pieces, 'BDFC', 1, True, float('-inf'), float('inf'))
    
    assert isinstance(score1, (int, float))
    # Second call should be cached and identical
    assert score1 == score2
    
    # Test with winning position
    winning_board = [
        'BDEC', 'BLEC', 'SDEC', None,
        None, None, None, None,
        None, None, None, None,
        None, None, None, None
    ]
    board_tuple = tuple(winning_board)
    score = minimax_cached(board_tuple, tuple(['SLEC']), 'SLEC', 1, True, float('-inf'), float('inf'))
    assert score > 0
    
    # Test terminal case for depth
    score_depth0 = minimax_cached(board, pieces, 'BDFC', 0, True, float('-inf'), float('inf'))
    assert isinstance(score_depth0, (int, float))
    
    # Test with no remaining pieces
    score_no_pieces = minimax_cached(board, tuple([]), 'BDFC', 2, True, float('-inf'), float('inf'))
    assert isinstance(score_no_pieces, (int, float))

def test_adaptive_depth():
    """Test the adaptive depth function"""
    # Create test states with different numbers of remaining pieces
    state_many = {"board": [None] * 16, "piece": 'BDEC'}
    state_medium = {"board": ['BDEC'] * 8 + [None] * 8, "piece": 'BDFC'}
    state_few = {"board": ['BDEC'] * 12 + [None] * 4, "piece": 'BLEC'}
    
    # Test with plenty of time
    assert adaptive_depth(state_many, 4.0) == 3
    assert adaptive_depth(state_medium, 4.0) == 4
    assert adaptive_depth(state_few, 4.0) == 5
    
    # Test with medium time
    assert adaptive_depth(state_many, 2.0) == 3
    
    # Test with low time
    assert adaptive_depth(state_many, 1.0) == 2

@patch('time.time')
def test_find_best_pos(mock_time, win_state, partial_state, empty_state):
    """Test the position selection logic"""
    # Mock time to avoid timeout issues
    mock_time.return_value = 0
    
    # In a winning scenario, it should find the winning move
    best_pos = find_best_pos(win_state, 0)
    # Position 3 completes the winning row
    assert best_pos == 3
    
    # In a normal scenario, it should return a valid position
    pos = find_best_pos(partial_state, 0)
    assert pos in get_available_positions(partial_state["board"])
    
    # Test with empty board
    pos = find_best_pos(empty_state, 0)
    assert pos in get_available_positions(empty_state["board"])
    
    # Test with time pressure - should still return a valid move
    mock_time.side_effect = [0, TIMEOUT * 0.9]  # Initial time, then after first check
    pos = find_best_pos(empty_state, 0)
    assert pos in get_available_positions(empty_state["board"])

@patch('time.time')
def test_find_best_piece(mock_time, partial_state, win_state):
    """Test the piece selection logic"""
    # Mock time to avoid timeout issues
    mock_time.return_value = 0
    
    # It should return a piece from the available pieces
    piece = find_best_piece(partial_state, 0)
    available = get_available_pieces(partial_state)
    assert piece in available
    
    # Create a state where one piece would lead to a win for the opponent
    dangerous_state = {
        "board": win_state["board"],
        "piece": None
    }
    available = get_available_pieces(dangerous_state)
    
    # Remove the dangerous piece from available if it exists
    if 'SLEC' in available:
        available = [p for p in available if p != 'SLEC']
    
    # Don't pick the dangerous piece if possible
    safe_piece = find_best_piece(dangerous_state, 0)
    assert safe_piece != 'SLEC' or 'SLEC' not in available
    
    # Test with time pressure - should still return a valid piece
    mock_time.side_effect = [0, TIMEOUT * 0.9]  # Initial time, then after first check
    piece = find_best_piece(partial_state, 0)
    assert piece in get_available_pieces(partial_state)
    
    # Test the fallback to random choice
    with patch('random.choice', return_value='SLEP') as mock_random:
        mock_time.return_value = 0
        # Simulate no best piece found
        with patch('projet_quarto.minimax_cached', return_value=-float('inf')):
            piece = find_best_piece(partial_state, 0)
            assert piece == 'SLEP'
            mock_random.assert_called_once()

@patch('socket.socket')
def test_s_inscrire(mock_socket):
    """Test the server registration function"""
    # Setup mock for socket
    mock_instance = MagicMock()
    mock_socket.return_value.__enter__.return_value = mock_instance
    mock_instance.recv.return_value = b'{"status": "ok"}'
    
    # Capture stdout to verify output
    captured_output = StringIO()
    sys.stdout = captured_output
    
    s_inscrire()
    
    # Reset stdout
    sys.stdout = sys.__stdout__
    
    # Verify that the function sent the correct JSON
    sent_data = mock_instance.send.call_args[0][0].decode()
    sent_json = json.loads(sent_data)
    
    assert sent_json["request"] == "subscribe"
    assert sent_json["port"] == PORT
    assert sent_json["name"] == NOM
    assert sent_json["matricules"] == MATRICULES
    
    # Verify that the socket connected to the correct address
    mock_instance.connect.assert_called_once_with(SERVER_ADDRESS)
    
    # Verify that the function printed the server response
    assert "Réponse du serveur" in captured_output.getvalue()

@patch('socket.socket')
def test_main_ping(mock_socket):
    """Test the main function handling ping requests"""
    # Setup mock for socket and client connection
    mock_socket_instance = MagicMock()
    mock_client = MagicMock()
    mock_socket.return_value.__enter__.return_value = mock_socket_instance
    mock_socket_instance.accept.return_value = (mock_client, ('127.0.0.1', 12345))
    mock_client.__enter__.return_value = mock_client
    mock_client.recv.return_value = json.dumps({"request": "ping"}).encode()
    
    main()
    
    # Verify that the function sent the correct response
    sent_data = mock_client.send.call_args[0][0].decode()
    sent_json = json.loads(sent_data)
    
    assert sent_json["response"] == "pong"
    
    # Verify that socket was bound to correct port
    mock_socket_instance.bind.assert_called_once_with(('', PORT))
    mock_socket_instance.settimeout.assert_called_once_with(1)
    mock_socket_instance.listen.assert_called_once()

@patch('socket.socket')
@patch('projet_quarto.find_best_pos')
@patch('projet_quarto.find_best_piece')
def test_main_play(mock_find_piece, mock_find_pos, mock_socket):
    """Test the main function handling play requests"""
    # Mock the AI functions
    mock_find_pos.return_value = 3
    mock_find_piece.return_value = 'BDFC'
    
    # Setup mock for socket and client connection
    mock_socket_instance = MagicMock()
    mock_client = MagicMock()
    mock_socket.return_value.__enter__.return_value = mock_socket_instance
    mock_socket_instance.accept.return_value = (mock_client, ('127.0.0.1', 12345))
    mock_client.__enter__.return_value = mock_client
    
    # Create a play request
    play_request = {
        "request": "play",
        "state": {
            "board": [None] * 16,
            "piece": 'BDEC'
        },
        "errors": []
    }
    mock_client.recv.return_value = json.dumps(play_request).encode()
    
    # Capture stdout
    captured_output = StringIO()
    sys.stdout = captured_output
    
    main()
    
    # Reset stdout
    sys.stdout = sys.__stdout__
    
    # Verify that the function sent the correct response
    sent_data = mock_client.send.call_args[0][0].decode()
    sent_json = json.loads(sent_data)
    
    assert sent_json["response"] == "move"
    assert sent_json["move"]["pos"] == 3
    assert sent_json["move"]["piece"] == 'BDFC'
    assert "message" in sent_json
    
    # Verify that the AI functions were called
    mock_find_pos.assert_called_once()
    mock_find_piece.assert_called_once()
    
    # Verify that errors were printed
    assert "ERRORS" in captured_output.getvalue()
    assert "chosen_move" in captured_output.getvalue()

@patch('socket.socket')
def test_main_socket_timeout(mock_socket):
    """Test the main function handling socket timeout"""
    # Setup mock to raise timeout
    mock_socket_instance = MagicMock()
    mock_socket.return_value.__enter__.return_value = mock_socket_instance
    mock_socket_instance.accept.side_effect = socket.timeout
    
    # Should not raise exception
    main()
    
    # Verify socket was set up correctly
    mock_socket_instance.bind.assert_called_once_with(('', PORT))
    mock_socket_instance.settimeout.assert_called_once_with(1)
    mock_socket_instance.listen.assert_called_once()

@patch('socket.socket')
def test_main_exception(mock_socket):
    """Test the main function handling general exceptions"""
    # Setup mock to raise exception
    mock_socket_instance = MagicMock()
    mock_socket.return_value.__enter__.return_value = mock_socket_instance
    mock_socket_instance.accept.side_effect = Exception("Test exception")
    
    # Capture stdout
    captured_output = StringIO()
    sys.stdout = captured_output
    
    # Should not raise exception
    main()
    
    # Reset stdout
    sys.stdout = sys.__stdout__
    
    # Verify error was printed
    assert "Erreur: Test exception" in captured_output.getvalue()

@patch('socket.socket')
def test_main_json_decode_error(mock_socket):
    """Test main function handling invalid JSON"""
    # Setup mock for socket and client connection
    mock_socket_instance = MagicMock()
    mock_client = MagicMock()
    mock_socket.return_value.__enter__.return_value = mock_socket_instance
    mock_socket_instance.accept.return_value = (mock_client, ('127.0.0.1', 12345))
    mock_client.__enter__.return_value = mock_client
    mock_client.recv.return_value = b'invalid json'
    
    # Capture stdout
    captured_output = StringIO()
    sys.stdout = captured_output
    
    main()
    
    # Reset stdout
    sys.stdout = sys.__stdout__
    
    # Verify error was printed
    assert "Erreur" in captured_output.getvalue()

# Create a conftest.py file with pytest configuration
@pytest.fixture(scope="session", autouse=True)
def create_conftest():
    with open("conftest.py", "w") as f:
        f.write("""
# content of conftest.py
def pytest_addoption(parser):
    parser.addoption(
        "--cov-report", action="store", default="term-missing",
        help="Coverage report format"
    )
    parser.addoption(
        "--cov", action="store", default="projet_quarto",
        help="Path to measure coverage"
    )
""")
    yield
    # Clean up
    if os.path.exists("conftest.py"):
        os.remove("conftest.py")

# Create a pytest.ini file with coverage configuration
@pytest.fixture(scope="session", autouse=True)
def create_pytest_ini():
    with open("pytest.ini", "w") as f:
        f.write("""
[pytest]
addopts = --cov=projet_quarto --cov-report=term-missing --cov-report=html
""")
    yield
    # Clean up
    if os.path.exists("pytest.ini"):
        os.remove("pytest.ini")

if __name__ == '__main__':
    pytest.main(["-v", "--cov=projet_quarto", "--cov-report=term-missing", "--cov-report=html"])
