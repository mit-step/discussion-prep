import { useEffect, useRef, useState } from "react";
import { useUser } from "../context/UserContext";
import { avatarColorFor } from "../utils/avatarColor";

export function ProfileMenu() {
  const { user, logout } = useUser();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  if (!user) return null;
  const initial = user.name.trim().charAt(0).toUpperCase() || "?";

  return (
    <div className="profile-menu" ref={ref}>
      <button
        type="button"
        className="avatar-badge"
        style={{ background: avatarColorFor(user.email) }}
        onClick={() => setOpen((o) => !o)}
        title={user.name}
      >
        {initial}
      </button>
      {open && (
        <div className="profile-dropdown">
          <div className="profile-dropdown-name">{user.name}</div>
          <button type="button" className="profile-dropdown-logout" onClick={logout}>
            Log out
          </button>
        </div>
      )}
    </div>
  );
}
