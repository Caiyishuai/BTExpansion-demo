(define (domain neg-precond)
  (:requirements :strips :typing :negative-preconditions)

  (:types item)

  (:predicates
    (painted ?i - item)
    (dirty ?i - item)
    (dry ?i - item)
  )

  ;; 只能给"不脏"的物体上漆 —— 这是真正的负前提
  (:action paint
    :parameters (?i - item)
    :precondition (and (not (dirty ?i)) (dry ?i))
    :effect (and (painted ?i))
    :cost 1
  )

  (:action wash
    :parameters (?i - item)
    :precondition (and (dirty ?i))
    :effect (and (not (dirty ?i)) (not (dry ?i)))
    :cost 1
  )

  (:action dry-it
    :parameters (?i - item)
    :precondition (and (not (dirty ?i)))
    :effect (and (dry ?i))
    :cost 1
  )
)
