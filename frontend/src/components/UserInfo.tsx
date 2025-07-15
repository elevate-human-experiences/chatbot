import { User } from "lucide-react";

interface UserInfoProps {
  user: {
    id: string;
    name: string;
    email: string;
  } | null;
  hideDetails?: boolean;
}

export function UserInfo({ user, hideDetails = false }: UserInfoProps) {
  return (
    <div
      className={hideDetails ? "p-4 flex justify-center items-center" : "p-4"}
      style={{ maxWidth: !hideDetails ? "279px" : "89px" }}
    >
      <div
        className={hideDetails ? "flex items-center justify-center" : "flex items-center space-x-3"}
        style={hideDetails ? { width: "100%" } : {}}
      >
        <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
          <User className="w-4 h-4 text-white" />
        </div>
        {!hideDetails && (
          <div>
            {user ? (
              <>
                <div className="font-medium text-sm text-gray truncate">{user.name}</div>
                <div className="text-xs text-gray-400 truncate">{user.email}</div>
              </>
            ) : (
              <div className="text-xs text-gray-400">No user logged in</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
