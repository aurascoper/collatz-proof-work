/-!
  Machine-checked Lean 4 formalization of Hercher (arXiv:2201.00406v3, Definitions 1, 5, 6)
  Collatz parity-word invariants:
  1. Odd-step count mOdd(w) = #{i : w_i = true}
  2. Cyclic local minima mMin(w) = #{i : (w_i, w_{i+1}, w_{i+2}) = (false, false, true)}
  3. Shortcut-map correspondence T(n) = (3n+1)/2 on cyclically admissible words (no adjacent 11)
  4. Unconditional bound mMin(w) <= mOdd(w)
  5. Exact separation witness "00010101" (mOdd = 3, mMin = 1)
  6. Cyclic rotation invariance of both mOdd and mMin
  Zero axioms beyond Lean core; zero sorry.
-/

def mOdd : List Bool -> Nat
  | [] => 0
  | true :: xs => 1 + mOdd xs
  | false :: xs => mOdd xs

def rotateLeft : List Bool -> Nat -> List Bool
  | [], _ => []
  | xs, 0 => xs
  | x :: xs, n + 1 => rotateLeft (xs ++ [x]) n

def tripleAt (w : List Bool) (i : Nat) : Bool × Bool × Bool :=
  match rotateLeft w i with
  | a :: b :: c :: _ => (a, b, c)
  | _ => (true, true, true)

def isLocalMinTriple : (Bool × Bool × Bool) -> Bool
  | (false, false, true) => true
  | _ => false

def mMin (w : List Bool) : Nat :=
  if w.length < 3 then 0
  else ((List.range w.length).filter (fun i => isLocalMinTriple (tripleAt w i))).length

/-- Ordinary-Collatz cyclic admissibility: no adjacent (true, true) in cyclic window. -/
def cyclicAdmissible (w : List Bool) : Bool :=
  if w.length < 2 then true
  else
    (List.range w.length).all (fun i =>
      match rotateLeft w i with
      | true :: true :: _ => false
      | _ => true)

/-- Ordinary affine step (3n+1 for true, n/2 for false) vs shortcut upward step (3n+1)/2. -/
def ordinaryStep (b : Bool) (n : Nat) : Nat :=
  if b then 3 * n + 1 else n / 2

def shortcutUpStep (n : Nat) : Nat :=
  (3 * n + 1) / 2

theorem ordinary_one_zero_eq_shortcutUp (n : Nat) :
    ordinaryStep false (ordinaryStep true n) = shortcutUpStep n := by
  rfl

theorem rotateLeft_zero (w : List Bool) : rotateLeft w 0 = w := by
  cases w <;> rfl

theorem rotateLeft_nil (k : Nat) : rotateLeft [] k = [] := by
  cases k <;> rfl

theorem rotateLeft_length (w : List Bool) (k : Nat) :
    (rotateLeft w k).length = w.length := by
  induction k generalizing w with
  | zero => simp [rotateLeft_zero]
  | succ k ih =>
      cases w with
      | nil => rfl
      | cons x xs =>
          simp [rotateLeft, ih, List.length_append]

theorem rotateLeft_add (w : List Bool) (a b : Nat) :
    rotateLeft (rotateLeft w a) b = rotateLeft w (a + b) := by
  induction a generalizing w with
  | zero => simp [rotateLeft_zero]
  | succ a ih =>
      cases w with
      | nil =>
          simp [rotateLeft_nil]
      | cons x xs =>
          have h : a + 1 + b = (a + b) + 1 := by omega
          rw [h]
          simp only [rotateLeft]
          exact ih (xs ++ [x])

theorem rotateLeft_self_length (w : List Bool) :
    rotateLeft w w.length = w := by
  suffices h : forall (a b : List Bool), rotateLeft (a ++ b) a.length = b ++ a by
    have := h w []
    simpa using this
  intro a b
  induction a generalizing b with
  | nil => simp [rotateLeft_zero]
  | cons x xs ih =>
      simp only [List.length_cons, List.cons_append, rotateLeft]
      have h1 : xs.append b ++ [x] = xs ++ (b ++ [x]) := List.append_assoc xs b [x]
      rw [h1]
      have h2 := ih (b ++ [x])
      simpa [List.append_assoc] using h2

theorem mOdd_append (xs ys : List Bool) :
    mOdd (xs ++ ys) = mOdd xs + mOdd ys := by
  induction xs with
  | nil => simp [mOdd]
  | cons x xs ih =>
      cases x <;> simp [mOdd, ih] <;> omega

theorem mOdd_rotate_one (w : List Bool) :
    mOdd (rotateLeft w 1) = mOdd w := by
  cases w with
  | nil => rfl
  | cons x xs =>
      have hrot : rotateLeft (x :: xs) 1 = xs ++ [x] := by
        simp [rotateLeft, rotateLeft_zero]
      rw [hrot, mOdd_append]
      cases x <;> simp [mOdd] <;> omega

theorem mOdd_rotate_invariant (w : List Bool) (k : Nat) :
    mOdd (rotateLeft w k) = mOdd w := by
  induction k generalizing w with
  | zero => simp [rotateLeft_zero]
  | succ k ih =>
      have h : k + 1 = 1 + k := by omega
      rw [h, <- rotateLeft_add]
      rw [ih (rotateLeft w 1), mOdd_rotate_one w]

private theorem map_shift_rotate_one {α : Type} (f : Nat -> α) (n : Nat) :
    (List.range (n + 1)).map (fun i => f (i + 1)) =
      ((List.range n).map (fun i => f (i + 1))) ++ [f (n + 1)] := by
  rw [List.range_succ, List.map_append]
  simp

private theorem map_head_tail {α : Type} (f : Nat -> α) (n : Nat) :
    (List.range (n + 1)).map f =
      f 0 :: (List.range n).map (fun i => f (i + 1)) := by
  induction n with
  | zero => simp [List.range_succ]
  | succ n ih =>
      rw [List.range_succ, List.map_append, ih]
      simp [List.range_succ, List.map_append]

private theorem filter_map_length {α : Type} (l : List Nat) (f : Nat -> α) (p : α -> Bool) :
    (l.filter (fun i => p (f i))).length = ((l.map f).filter p).length := by
  induction l with
  | nil => simp
  | cons x xs ih =>
      simp only [List.filter_cons, List.map_cons]
      cases p (f x) <;> simp [ih]

private theorem filter_rotate_one_length {α : Type} (p : α -> Bool) (x : α) (xs : List α) :
    ((xs ++ [x]).filter p).length = ((x :: xs).filter p).length := by
  rw [List.filter_append]
  simp only [List.filter_cons, List.length_append]
  cases p x <;> simp <;> omega

private theorem filter_shift_periodic_length {α : Type} (f : Nat -> α) (p : α -> Bool)
    (n : Nat) (hper : f (n + 1) = f 0) :
    ((List.range (n + 1)).filter (fun i => p (f (i + 1)))).length =
      ((List.range (n + 1)).filter (fun i => p (f i))).length := by
  rw [filter_map_length, filter_map_length]
  rw [map_shift_rotate_one f n, map_head_tail f n, hper]
  exact filter_rotate_one_length p (f 0) ((List.range n).map (fun i => f (i + 1)))

theorem mMin_rotate_one (w : List Bool) :
    mMin (rotateLeft w 1) = mMin w := by
  unfold mMin
  by_cases hlen : w.length < 3
  · have hlen1 : (rotateLeft w 1).length < 3 := by simpa [rotateLeft_length] using hlen
    simp [hlen, hlen1]
  · have hlen1 : ¬ ((rotateLeft w 1).length < 3) := by rw [rotateLeft_length]; exact hlen
    simp only [hlen, hlen1, ↓reduceIte, rotateLeft_length]
    obtain ⟨m, hm⟩ : ∃ m, w.length = m + 1 := ⟨w.length - 1, by omega⟩
    have hrot : ∀ i, tripleAt (rotateLeft w 1) i = tripleAt w (i + 1) := by
      intro i
      simp only [tripleAt, rotateLeft_add]
      have h : 1 + i = i + 1 := by omega
      rw [h]
    have hper : tripleAt w (m + 1) = tripleAt w 0 := by
      rw [<- hm]
      simp only [tripleAt, rotateLeft_self_length, rotateLeft_zero]
    simp only [hrot, hm]
    exact filter_shift_periodic_length (tripleAt w) isLocalMinTriple m hper

theorem mMin_rotate_invariant (w : List Bool) (k : Nat) :
    mMin (rotateLeft w k) = mMin w := by
  induction k generalizing w with
  | zero => simp [rotateLeft_zero]
  | succ k ih =>
      have h : k + 1 = 1 + k := by omega
      rw [h, <- rotateLeft_add]
      rw [ih (rotateLeft w 1), mMin_rotate_one w]

private theorem rotateLeft_ge_three_cons (w : List Bool) (hlen : ¬ w.length < 3) (i : Nat) :
    ∃ a b c rest, rotateLeft w i = a :: b :: c :: rest := by
  have hl : (rotateLeft w i).length >= 3 := by rw [rotateLeft_length]; omega
  match h : rotateLeft w i with
  | a :: b :: c :: rest => exact ⟨a, b, c, rest, rfl⟩
  | [] => simp [h] at hl
  | [_] => simp [h] at hl
  | [_, _] => simp [h] at hl

private theorem localMin_implies_head_true_plus2 (w : List Bool) (hlen : ¬ w.length < 3) (i : Nat)
    (hm : isLocalMinTriple (tripleAt w i) = true) :
    (rotateLeft w (i + 2)).headD false = true := by
  obtain ⟨a, b, c, rest, hrot⟩ := rotateLeft_ge_three_cons w hlen i
  have ht : tripleAt w i = (a, b, c) := by simp [tripleAt, hrot]
  rw [ht] at hm
  have hc : c = true := by
    cases a <;> cases b <;> cases c <;> simp [isLocalMinTriple] at hm ⊢
  have h2 : rotateLeft w (i + 2) = rotateLeft (rotateLeft w i) 2 := by
    rw [rotateLeft_add]
  rw [h2, hrot]
  simp [rotateLeft, hc]

private theorem filter_le_of_imp {α : Type} (l : List α) (p q : α -> Bool)
    (himp : ∀ x, p x = true -> q x = true) :
    (l.filter p).length <= (l.filter q).length := by
  induction l with
  | nil => simp
  | cons x xs ih =>
      simp only [List.filter_cons]
      cases hp : p x with
      | false =>
          cases q x <;> simp <;> omega
      | true =>
          have hq : q x = true := himp x hp
          simp [hq]
          omega

private theorem range_headD_map_take (u : List Bool) (n : Nat) (hn : n <= u.length) :
    (List.range n).map (fun i => (rotateLeft u i).headD false) = u.take n := by
  induction n generalizing u with
  | zero => simp
  | succ n ih =>
      cases u with
      | nil => simp at hn
      | cons x xs =>
          rw [map_head_tail (fun i => (rotateLeft (x :: xs) i).headD false) n]
          have h0 : (rotateLeft (x :: xs) 0).headD false = x := rfl
          rw [h0]
          simp only [List.take_succ_cons]
          congr 1
          have hfn : (fun i => (rotateLeft (x :: xs) (i + 1)).headD false) =
              (fun i => (rotateLeft (xs ++ [x]) i).headD false) := by
            funext i
            have h1 : i + 1 = 1 + i := by omega
            have heq : rotateLeft (x :: xs) (i + 1) = rotateLeft (xs ++ [x]) i := by
              rw [h1, <- rotateLeft_add]
              simp [rotateLeft, rotateLeft_zero]
            rw [heq]
          have hstep : (List.range n).map (fun i => (rotateLeft (x :: xs) (i + 1)).headD false) =
              (List.range n).map (fun i => (rotateLeft (xs ++ [x]) i).headD false) := by
            rw [hfn]
          rw [hstep]
          have hn1 : n <= xs.length := by
            simp only [List.length_cons] at hn
            omega
          have hlen1 : n <= (xs ++ [x]).length := by
            rw [List.length_append]
            omega
          rw [ih (xs ++ [x]) hlen1, List.take_append_of_le_length hn1]

private theorem filter_id_length_eq_mOdd (w : List Bool) :
    (w.filter id).length = mOdd w := by
  induction w with
  | nil => simp [mOdd]
  | cons x xs ih =>
      cases x <;> simp [mOdd, List.filter_cons, ih] <;> omega

private theorem range_headD_filter_eq_mOdd (w : List Bool) :
    ((List.range w.length).filter (fun i => (rotateLeft w i).headD false)).length = mOdd w := by
  have hm := filter_map_length (List.range w.length) (fun i => (rotateLeft w i).headD false) id
  simp only [id_eq] at hm
  rw [hm, range_headD_map_take w w.length (Nat.le_refl _), List.take_length]
  exact filter_id_length_eq_mOdd w

theorem mMin_le_mOdd (w : List Bool) :
    mMin w <= mOdd w := by
  unfold mMin
  by_cases hlen : w.length < 3
  · simp [hlen]
  · simp only [hlen, ↓reduceIte]
    have h1 : ((List.range w.length).filter (fun i => isLocalMinTriple (tripleAt w i))).length <=
        ((List.range w.length).filter (fun i => (rotateLeft w (i + 2)).headD false)).length :=
      filter_le_of_imp (List.range w.length)
        (fun i => isLocalMinTriple (tripleAt w i))
        (fun i => (rotateLeft w (i + 2)).headD false)
        (fun i hm => localMin_implies_head_true_plus2 w hlen i hm)
    obtain ⟨m, hm⟩ : ∃ m, w.length = m + 1 := ⟨w.length - 1, by omega⟩
    let g : Nat -> Bool := fun i => (rotateLeft w i).headD false
    have hper : g (m + 1) = g 0 := by
      rw [<- hm]
      simp [g, rotateLeft_self_length, rotateLeft_zero]
    have hshift1 : ((List.range (m + 1)).filter (fun i => g (i + 2))).length =
        ((List.range (m + 1)).filter (fun i => g (i + 1))).length := by
      have hper1 : (fun i => g (i + 1)) (m + 1) = (fun i => g (i + 1)) 0 := by
        have hstep : rotateLeft w (m + 1 + 1) = rotateLeft w 1 := by
          have : m + 1 + 1 = w.length + 1 := by omega
          rw [this, <- rotateLeft_add, rotateLeft_self_length]
        simp [g, hstep]
      exact filter_shift_periodic_length (fun i => g (i + 1)) id m hper1
    have hshift0 : ((List.range (m + 1)).filter (fun i => g (i + 1))).length =
        ((List.range (m + 1)).filter (fun i => g i)).length :=
      filter_shift_periodic_length g id m hper
    have hodd : ((List.range (m + 1)).filter (fun i => g i)).length = mOdd w := by
      rw [<- hm]
      exact range_headD_filter_eq_mOdd w
    have h1' : ((List.range (m + 1)).filter (fun i => isLocalMinTriple (tripleAt w i))).length <=
        ((List.range (m + 1)).filter (fun i => g (i + 2))).length := by
      rw [<- hm]
      exact h1
    rw [hm]
    omega

theorem witness_00010101_separates_mMin_and_mOdd :
    let w := [false, false, false, true, false, true, false, true]
    cyclicAdmissible w = true ∧ mOdd w = 3 ∧ mMin w = 1 ∧ mMin w < mOdd w := by
  decide

#print axioms ordinary_one_zero_eq_shortcutUp
#print axioms mOdd_rotate_invariant
#print axioms mMin_rotate_invariant
#print axioms mMin_le_mOdd
#print axioms witness_00010101_separates_mMin_and_mOdd
