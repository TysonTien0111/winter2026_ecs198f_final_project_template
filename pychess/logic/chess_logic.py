class ChessLogic:
    def __init__(self):
        """
        Initialize the ChessLogic Object. External fields are board and result

        board -> Two Dimensional List of string Representing the Current State of the Board
            P, R, N, B, Q, K - White Pieces

            p, r, n, b, q, k - Black Pieces

            '' - Empty Square

        result -> The current result of the game
            w - White Win

            b - Black Win

            d - Draw

            '' - Game In Progress
        """
        self.board = [
            ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
            ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
            ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R'],
        ]
        self.result = "" 
        self.turn = 'w'
        
        self.castling_rights = {
            'w': {'K': True, 'Q': True},
            'b': {'K': True, 'Q': True}
        }
        self.ep_target = None

    def play_move(self, move: str) -> str:
        """
        Function to make a move if it is a valid move. This function is called everytime a move in made on the board

        Args:
            move (str): The move which is proposed. The format is the following: starting_sqaure}{ending_square}
            
            i.e. e2e4 - This means that whatever piece is on E2 is moved to E4

        Returns:
            str: Extended Chess Notation for the move, if valid. Empty str if the move is invalid
        """
        if self.result != "":
            return ""
            
        if len(move) != 4:
            return ""
            
        start_sq, end_sq = move[0:2], move[2:4]
        sr, sc = self._parse_sq(start_sq)
        er, ec = self._parse_sq(end_sq)
        
        if (sr, sc) == (-1, -1) or (er, ec) == (-1, -1):
            return ""
            
        piece = self.board[sr][sc]
        if piece == "":
            return ""
            
        piece_color = 'w' if piece.isupper() else 'b'
        if piece_color != self.turn:
            return ""

        move_info = self._get_move_info(sr, sc, er, ec)
        if not move_info:
            return ""

        if self._leaves_king_in_check(sr, sc, er, ec, move_info):
            return ""

        notation = self._execute_move(sr, sc, er, ec, move_info, start_sq, end_sq, piece)

        self.turn = 'b' if self.turn == 'w' else 'w'
        self._update_result()

        return notation

    def _parse_sq(self, sq: str) -> tuple[int, int]:
        if len(sq) != 2: return -1, -1
        col = ord(sq[0].lower()) - ord('a')
        try:
            row = 8 - int(sq[1])
        except ValueError:
            return -1, -1
        if 0 <= col <= 7 and 0 <= row <= 7:
            return row, col
        return -1, -1

    def _get_move_info(self, sr, sc, er, ec):
        piece = self.board[sr][sc]
        color = 'w' if piece.isupper() else 'b'
        target = self.board[er][ec]
        
        if target != "":
            target_color = 'w' if target.isupper() else 'b'
            if color == target_color:
                return None
                
        ptype = piece.lower()
        
        if ptype == 'p':
            direction = -1 if color == 'w' else 1
            start_row = 6 if color == 'w' else 1
            promo_row = 0 if color == 'w' else 7
            
            if sc == ec:
                if target == "":
                    if er == sr + direction:
                        return {'type': 'normal' if er != promo_row else 'promo'}
                    if sr == start_row and er == sr + 2 * direction and self.board[sr + direction][sc] == "":
                        return {'type': 'double'}
            elif abs(sc - ec) == 1 and er == sr + direction:
                if target != "":
                    return {'type': 'capture' if er != promo_row else 'promo_capture'}
                elif self.ep_target == (er, ec):
                    return {'type': 'ep'}
        
        elif ptype == 'n':
            if (abs(sr - er), abs(sc - ec)) in [(1, 2), (2, 1)]:
                return {'type': 'capture' if target != "" else 'normal'}
                
        elif ptype in ['b', 'r', 'q']:
            dr, dc = er - sr, ec - sc
            if dr != 0: dr = dr // abs(dr)
            if dc != 0: dc = dc // abs(dc)
            
            if ptype == 'b' and (dr == 0 or dc == 0): return None
            if ptype == 'r' and (dr != 0 and dc != 0): return None
            
            curr_r, curr_c = sr + dr, sc + dc
            while (curr_r, curr_c) != (er, ec):
                if not (0 <= curr_r <= 7 and 0 <= curr_c <= 7): return None
                if self.board[curr_r][curr_c] != "": return None
                curr_r += dr
                curr_c += dc
                
            if curr_r == er and curr_c == ec:
                return {'type': 'capture' if target != "" else 'normal'}

        elif ptype == 'k':
            if max(abs(sr - er), abs(sc - ec)) == 1:
                return {'type': 'capture' if target != "" else 'normal'}
                
            if sr == er and abs(sc - ec) == 2 and target == "":
                row = 7 if color == 'w' else 0
                if sr == row:
                    if ec == 6 and self.castling_rights[color]['K']:
                        if self.board[row][5] == "" and self.board[row][6] == "":
                            return {'type': 'castle_K'}
                    elif ec == 2 and self.castling_rights[color]['Q']:
                        if self.board[row][1] == "" and self.board[row][2] == "" and self.board[row][3] == "":
                            return {'type': 'castle_Q'}
        return None

    def _leaves_king_in_check(self, sr, sc, er, ec, move_info):
        piece = self.board[sr][sc]
        color = 'w' if piece.isupper() else 'b'
        
        original_target = self.board[er][ec]
        original_ep = None
        ep_r, ep_c = -1, -1
        
        self.board[er][ec] = piece
        self.board[sr][sc] = ""
        
        if move_info['type'] == 'ep':
            ep_r, ep_c = (sr, ec)
            original_ep = self.board[ep_r][ep_c]
            self.board[ep_r][ep_c] = ""
            
        is_in_check = self._is_in_check(color)
        
        if move_info['type'] in ['castle_K', 'castle_Q']:
            if self._is_in_check(color):
                is_in_check = True
            else:
                mid_c = (sc + ec) // 2
                self.board[sr][mid_c] = piece
                self.board[er][ec] = ""
                if self._is_in_check(color):
                    is_in_check = True
                self.board[er][ec] = piece
                self.board[sr][mid_c] = ""
        
        self.board[sr][sc] = piece
        self.board[er][ec] = original_target
        if move_info['type'] == 'ep':
            self.board[ep_r][ep_c] = original_ep
            
        return is_in_check

    def _is_in_check(self, color):
        king_piece = 'K' if color == 'w' else 'k'
        kr, kc = -1, -1
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == king_piece:
                    kr, kc = r, c
                    break
            if kr != -1: break
            
        if kr == -1: return False
        
        opp_color = 'b' if color == 'w' else 'w'
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p != "" and ('w' if p.isupper() else 'b') == opp_color:
                    if self._get_move_info(r, c, kr, kc) is not None:
                        return True
        return False

    def _execute_move(self, sr, sc, er, ec, move_info, start_sq, end_sq, piece):
        color = 'w' if piece.isupper() else 'b'
        target = self.board[er][ec]
        
        is_capture = (target != "") or (move_info['type'] == 'ep')
        
        # Determine the piece string for notation.
        # Following the examples provided, we'll use lower-case if piece is a white knight as in 'ng1f3'.
        # We'll stick to piece.lower() to perfectly match the 'ng1f3' example, 
        # though standard algebraic notation usually uses uppercase N.
        piece_str = piece.lower() if piece.lower() != 'p' else ""
        
        notation = ""
        if move_info['type'] == 'castle_K':
            notation = "O-O"
            self.board[er][5] = self.board[er][7]
            self.board[er][7] = ""
        elif move_info['type'] == 'castle_Q':
            notation = "O-O-O"
            self.board[er][3] = self.board[er][0]
            self.board[er][0] = ""
        else:
            notation = f"{piece_str}{start_sq}{'x' if is_capture else ''}{end_sq}"
            
        self.board[er][ec] = piece
        self.board[sr][sc] = ""
        
        if move_info['type'] == 'ep':
            self.board[sr][ec] = ""
            
        if move_info['type'] in ['promo', 'promo_capture']:
            promoted_piece = 'Q' if color == 'w' else 'q'
            self.board[er][ec] = promoted_piece
            notation += "=Q"
            
        if piece == 'K':
            self.castling_rights['w']['K'] = False
            self.castling_rights['w']['Q'] = False
        elif piece == 'k':
            self.castling_rights['b']['K'] = False
            self.castling_rights['b']['Q'] = False
        elif piece == 'R':
            if (sr, sc) == (7, 0): self.castling_rights['w']['Q'] = False
            if (sr, sc) == (7, 7): self.castling_rights['w']['K'] = False
        elif piece == 'r':
            if (sr, sc) == (0, 0): self.castling_rights['b']['Q'] = False
            if (sr, sc) == (0, 7): self.castling_rights['b']['K'] = False
            
        if target == 'R':
            if (er, ec) == (7, 0): self.castling_rights['w']['Q'] = False
            if (er, ec) == (7, 7): self.castling_rights['w']['K'] = False
        elif target == 'r':
            if (er, ec) == (0, 0): self.castling_rights['b']['Q'] = False
            if (er, ec) == (0, 7): self.castling_rights['b']['K'] = False
            
        if move_info['type'] == 'double':
            self.ep_target = (sr + (-1 if color == 'w' else 1), sc)
        else:
            self.ep_target = None
            
        return notation

    def _update_result(self):
        has_legal_moves = False
        for sr in range(8):
            for sc in range(8):
                p = self.board[sr][sc]
                if p != "" and ('w' if p.isupper() else 'b') == self.turn:
                    for er in range(8):
                        for ec in range(8):
                            info = self._get_move_info(sr, sc, er, ec)
                            if info and not self._leaves_king_in_check(sr, sc, er, ec, info):
                                has_legal_moves = True
                                break
                        if has_legal_moves: break
                if has_legal_moves: break
            if has_legal_moves: break
            
        if not has_legal_moves:
            if self._is_in_check(self.turn):
                self.result = 'w' if self.turn == 'b' else 'b'
            else:
                self.result = 'd'
