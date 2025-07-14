import { User } from "lucide-react";

interface UserInfoProps {
  user: {
    id: string;
    name: string;
    email: string;
  } | null;
}

export function UserInfo({ user }: UserInfoProps) {
  return (
    <div className="p-4">
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
          <User className="w-4 h-4 text-white" />
        </div>
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
      </div>
    </div>
  );
}
