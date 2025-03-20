import mongoose, { Document, Schema } from 'mongoose';
import bcrypt from 'bcrypt';
import { nanoid } from 'nanoid';

// 用户角色枚举
export enum UserRole {
    USER = 'USER',
    PREMIUM = 'PREMIUM',
    ADMIN = 'ADMIN'
}

// 用户状态枚举
export enum UserStatus {
    ACTIVE = 'active',
    INACTIVE = 'inactive',
    SUSPENDED = 'suspended'
}

// 用户文档接口
export interface UserDocument extends Document {
    email: string;
    password: string;
    name: string;
    role: UserRole;
    status: UserStatus;
    lastLogin?: Date;
    createdAt: Date;
    updatedAt: Date;
    verified: boolean;
    verificationToken?: string;
    passwordResetToken?: string;
    passwordResetExpires?: Date;
    apiQuota?: {
        limit: number;
        remaining: number;
        resetDate: Date;
    };
    preferences?: {
        theme: string;
        language: string;
        notifications: boolean;
    };

    // 实例方法
    comparePassword(candidatePassword: string): Promise<boolean>;
    generateVerificationToken(): string;
    generatePasswordResetToken(): Promise<string>;
}

// 用户Schema定义
const UserSchema = new Schema<UserDocument>({
    email: {
        type: String,
        required: true,
        unique: true,
        trim: true,
        lowercase: true,
        validate: {
            validator: function (v: string) {
                return /^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/.test(v);
            },
            message: (props: { value: string }) => `${props.value} 不是有效的邮箱地址`
        }
    },
    password: {
        type: String,
        required: true,
        minlength: 6
    },
    name: {
        type: String,
        required: true,
        trim: true
    },
    role: {
        type: String,
        enum: Object.values(UserRole),
        default: UserRole.USER
    },
    status: {
        type: String,
        enum: Object.values(UserStatus),
        default: UserStatus.ACTIVE
    },
    lastLogin: {
        type: Date
    },
    verified: {
        type: Boolean,
        default: false
    },
    verificationToken: {
        type: String
    },
    passwordResetToken: {
        type: String
    },
    passwordResetExpires: {
        type: Date
    },
    apiQuota: {
        limit: {
            type: Number,
            default: 50
        },
        remaining: {
            type: Number,
            default: 50
        },
        resetDate: {
            type: Date,
            default: Date.now
        }
    },
    preferences: {
        theme: {
            type: String,
            default: 'light'
        },
        language: {
            type: String,
            default: 'zh-CN'
        },
        notifications: {
            type: Boolean,
            default: true
        }
    }
}, {
    timestamps: true,
    toJSON: {
        transform: function (_doc, ret) {
            delete ret.password;
            delete ret.__v;
            delete ret.verificationToken;
            delete ret.passwordResetToken;
            delete ret.passwordResetExpires;
            return ret;
        }
    }
});

// 创建索引
UserSchema.index({ email: 1 });
UserSchema.index({ role: 1 });
UserSchema.index({ status: 1 });

// 密码加密中间件
UserSchema.pre('save', async function (next) {
    // 只有当密码被修改或是新用户时才进行哈希
    const user = this as UserDocument;
    if (!user.isModified('password')) return next();

    try {
        // 生成盐并哈希密码
        const salt = await bcrypt.genSalt(10);
        user.password = await bcrypt.hash(user.password, salt);
        next();
    } catch (error: any) {
        next(error);
    }
});

// 比较密码
UserSchema.methods.comparePassword = async function (candidatePassword: string): Promise<boolean> {
    const user = this as UserDocument;
    return bcrypt.compare(candidatePassword, user.password);
};

// 生成验证令牌
UserSchema.methods.generateVerificationToken = function (): string {
    const user = this as UserDocument;
    const token = nanoid(32);
    user.verificationToken = token;
    return token;
};

// 生成密码重置令牌
UserSchema.methods.generatePasswordResetToken = async function (): Promise<string> {
    const user = this as UserDocument;
    const token = nanoid(32);
    user.passwordResetToken = token;
    user.passwordResetExpires = new Date(Date.now() + 3600000); // 1小时后过期
    await user.save();
    return token;
};

// 导出模型
const User = mongoose.model<UserDocument>('User', UserSchema);

export default User; 